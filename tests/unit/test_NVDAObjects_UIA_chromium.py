# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NV Access Limited, Juanjo M
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt

"""Regression tests for Chromium UIA container range boundaries."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import browseMode
import textInfos
from controlTypes import OutputReason
from NVDAObjects.UIA.chromium import ChromiumUIATreeInterceptor
from textInfos.offsets import Offsets

from .textProvider import BasicTextInfo, BasicTextProvider


class TestChromiumContainerRange(unittest.TestCase):
	"""Exercise normalization and the existing navigation commands without COM."""

	def setUp(self) -> None:
		self.interceptor = object.__new__(ChromiumUIATreeInterceptor)

	def _prepareContainer(self, story: str, start: int, end: int) -> BasicTextInfo:
		self.provider = BasicTextProvider(text=story, selection=(start, start))
		container = self.provider.makeTextInfo(Offsets(start, end))
		self.interceptor._iterNodesByType = Mock(return_value=iter([SimpleNamespace(textInfo=container)]))
		self.interceptor.makeTextInfo = self.provider.makeTextInfo
		return container

	def _getContainer(self) -> textInfos.TextInfo | None:
		caret = self.provider.makeTextInfo(textInfos.POSITION_CARET)
		result = self.interceptor.getEnclosingContainerRange(caret)
		self.assertEqual(self.provider.selectionOffsets, caret.offsets)
		self.interceptor._iterNodesByType.assert_called_once()
		self.assertEqual(("container", "up"), self.interceptor._iterNodesByType.call_args.args[:2])
		return result

	def test_includesOmittedLineEnding(self) -> None:
		for lineEnding in ("\n", "\r"):
			with self.subTest(lineEnding=lineEnding):
				self._prepareContainer(f"Before\nList{lineEnding}After", 7, 11)
				container = self._getContainer()
				self.assertEqual(f"List{lineEnding}", container.text)
				container.collapse(end=True)
				container.expand(textInfos.UNIT_CHARACTER)
				self.assertEqual("A", container.text)

	def test_includesCRLFCharacterUnit(self) -> None:
		"""Accept a provider exposing CRLF as one unit, unlike BasicTextInfo."""
		self._prepareContainer("List\r\nAfter", 0, 4)
		originalExpand = BasicTextInfo.expand

		def expandCRLF(info: BasicTextInfo, unit: str) -> None:
			originalExpand(info, unit)
			if unit == textInfos.UNIT_CHARACTER and info.text == "\r":
				info._endOffset += 1

		with patch.object(BasicTextInfo, "expand", new=expandCRLF):
			self.assertEqual((0, 6), self._getContainer().offsets)

	def test_doesNotSkipFollowingContent(self) -> None:
		for following in ("After", " After", "\tAfter", "\u00a0After", "\ufffcAfter", "😀After"):
			with self.subTest(following=following):
				original = self._prepareContainer(f"List{following}", 0, 4)
				container = self._getContainer()
				self.assertIs(original, container)
				self.assertEqual((0, 4), container.offsets)

	def test_keepsAlreadyCompleteRange(self) -> None:
		self._prepareContainer("List\nAfter", 0, 5)
		self.assertEqual((0, 5), self._getContainer().offsets)

	def test_keepsEmptyLineAfterCompleteRange(self) -> None:
		self._prepareContainer("List\n\nAfter", 0, 5)
		self.assertEqual((0, 5), self._getContainer().offsets)

	def test_keepsEmptyContainerBeforeEmptyLine(self) -> None:
		self._prepareContainer("\nAfter", 0, 0)
		self.assertEqual((0, 0), self._getContainer().offsets)

	def test_doesNotSkipAdditionalEmptyLines(self) -> None:
		self._prepareContainer("List\n\nAfter", 0, 4)
		self.assertEqual((0, 5), self._getContainer().offsets)

	def test_keepsEndOfDocument(self) -> None:
		for story in ("List", "List\n", ""):
			with self.subTest(story=story):
				self._prepareContainer(story, 0, len(story))
				self.assertEqual((0, len(story)), self._getContainer().offsets)

	def test_doesNotUseCharacterBeforeContainerEnd(self) -> None:
		"""Some providers expand a collapsed document end to the previous character."""
		container = self._prepareContainer("List\n", 0, 5)
		probe = container.copy()
		previousCharacter = self.provider.makeTextInfo(Offsets(4, 5))
		with (
			patch.object(container, "copy", return_value=probe),
			patch.object(
				probe,
				"expand",
				side_effect=lambda unit: probe.setEndPoint(previousCharacter, "startToStart"),
			),
			patch.object(container, "setEndPoint", wraps=container.setEndPoint) as setEndPoint,
		):
			self.assertIs(container, self._getContainer())
		setEndPoint.assert_not_called()

	def test_preservesNearestContainer(self) -> None:
		nearest = self._prepareContainer("Outer\nInner\nStill outer\nAfter", 6, 11)
		outer = self.provider.makeTextInfo(Offsets(0, 23))
		self.interceptor._iterNodesByType.return_value = iter(
			[SimpleNamespace(textInfo=nearest), SimpleNamespace(textInfo=outer)],
		)
		self.assertEqual((6, 12), self._getContainer().offsets)

	def test_preservesLandmarkFallback(self) -> None:
		landmark = self._prepareContainer("Region\nAfter", 0, 6)
		self.interceptor._iterNodesByType.side_effect = (
			iter(()),
			iter([SimpleNamespace(textInfo=landmark)]),
		)
		caret = self.provider.makeTextInfo(textInfos.POSITION_CARET)
		self.assertEqual("Region\n", self.interceptor.getEnclosingContainerRange(caret).text)
		self.assertEqual(
			["container", "landmark"],
			[call.args[0] for call in self.interceptor._iterNodesByType.call_args_list],
		)

	def test_noContainer(self) -> None:
		self._prepareContainer("After", 0, 0)
		self.interceptor._iterNodesByType.return_value = iter(())
		caret = self.provider.makeTextInfo(textInfos.POSITION_CARET)
		self.assertIsNone(self.interceptor.getEnclosingContainerRange(caret))

	def test_movePastEndReadsNextLine(self) -> None:
		"""Use the real command with the endpoint observed in Chrome's UIA provider."""
		contents = "• Alpha\n◦ Last nested item"
		self._prepareContainer(f"{contents}\nAfter ordinary", 0, len(contents))
		selected: list[BasicTextInfo] = []
		with (
			patch.object(
				self.interceptor,
				"_set_selection",
				side_effect=lambda info, **kwargs: selected.append(info.copy()),
			) as setSelection,
			patch.object(browseMode, "willSayAllResume", return_value=False),
			patch.object(browseMode.speech, "speakTextInfo") as speakTextInfo,
		):
			self.interceptor.script_movePastEndOfContainer(None)
		self.assertEqual((len(contents) + 1, len(contents) + 1), selected[0].offsets)
		self.assertEqual(OutputReason.QUICKNAV, setSelection.call_args.kwargs["reason"])
		self.assertEqual("After ordinary", speakTextInfo.call_args.args[0].text)

	def test_moveToStartPreservesStart(self) -> None:
		self._prepareContainer("Before\nList\nAfter", 7, 11)
		selected: list[BasicTextInfo] = []
		with (
			patch.object(
				self.interceptor,
				"_set_selection",
				side_effect=lambda info, **kwargs: selected.append(info.copy()),
			),
			patch.object(browseMode, "willSayAllResume", return_value=False),
			patch.object(browseMode.speech, "speakTextInfo") as speakTextInfo,
		):
			self.interceptor.script_moveToStartOfContainer(None)
		self.assertEqual((7, 7), selected[0].offsets)
		self.assertEqual("List\n", speakTextInfo.call_args.args[0].text)

	def test_movePastEndAtDocumentBottom(self) -> None:
		for story in ("List", "List\n"):
			with self.subTest(story=story):
				self._prepareContainer(story, 0, len(story))
				selected: list[BasicTextInfo] = []
				with (
					patch.object(
						self.interceptor,
						"_set_selection",
						side_effect=lambda info, selected=selected, **kwargs: selected.append(info.copy()),
					),
					patch.object(browseMode, "willSayAllResume", return_value=False),
					patch.object(browseMode.speech, "speakTextInfo"),
					patch.object(browseMode.ui, "message") as message,
				):
					self.interceptor.script_movePastEndOfContainer(None)
				message.assert_called_once_with("Bottom")
				last = self.provider.makeTextInfo(textInfos.POSITION_LAST)
				self.assertEqual(last.offsets, selected[0].offsets)

	def test_sayAllResumesAfterContainer(self) -> None:
		self._prepareContainer("List\nAfter", 0, 4)
		with (
			patch.object(self.interceptor, "_set_selection") as setSelection,
			patch.object(browseMode, "willSayAllResume", return_value=True),
			patch.object(browseMode.speech, "speakTextInfo") as speakTextInfo,
		):
			self.interceptor.script_movePastEndOfContainer(None)
		self.assertEqual((5, 5), setSelection.call_args.args[0].offsets)
		speakTextInfo.assert_not_called()
