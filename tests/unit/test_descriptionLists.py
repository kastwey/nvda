# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt

"""Description-list counts at the native-buffer and presentation boundaries."""

import unittest  # noqa: I001

import IAccessibleHandler  # noqa: F401 - Initialize before importing IAccessible object modules.
import config
import controlTypes
import oleacc
import textInfos
from braille.regions.properties import getControlFieldBraille
from controlTypes import OutputReason
from speech.speech import getControlFieldSpeech
from virtualBuffers.gecko_ia2 import Gecko_ia2_TextInfo
from virtualBuffers.MSHTML import MSHTMLTextInfo


class TestDescriptionListFields(unittest.TestCase):
	def test_ia2NamesArePreservedUnlessContentMatches(self) -> None:
		for tag in ("dt", "dd"):
			for duplicateFlag in (None, "false", "true"):
				with self.subTest(tag=tag, duplicateFlag=duplicateFlag):
					field = textInfos.ControlField(
						{
							"IAccessible::role": str(oleacc.ROLE_SYSTEM_LISTITEM),
							"IAccessible2::attribute_tag": tag,
							"IAccessible2::attribute_explicit-name": "true",
							"name": "Accessible label",
							"alwaysReportName": "true",
						},
					)
					if duplicateFlag is not None:
						field["nameIsDuplicate"] = duplicateFlag
					info = Gecko_ia2_TextInfo.__new__(Gecko_ia2_TextInfo)
					info._normalizeControlField(field)
					if duplicateFlag == "true":
						self.assertNotIn("name", field)
						self.assertNotIn("alwaysReportName", field)
					else:
						self.assertEqual("Accessible label", field["name"])
						self.assertTrue(field["alwaysReportName"])
					self.assertNotIn("nameIsDuplicate", field)
					formatConfig = config.conf["documentFormatting"].copy()
					formatConfig["reportLists"] = True
					for reason in (OutputReason.CARET, OutputReason.SAYALL, OutputReason.QUICKNAV):
						fieldType = "end_relative" if reason == OutputReason.QUICKNAV else "start_relative"
						speech = getControlFieldSpeech(field, [], fieldType, formatConfig, reason=reason)
						self.assertEqual(duplicateFlag != "true", "Accessible label" in speech)
					braille = getControlFieldBraille(None, field, [], True, formatConfig)
					self.assertEqual(duplicateFlag != "true", "Accessible label" in braille)

	def test_ia2DuplicateFlagDoesNotChangeOverriddenRoles(self) -> None:
		field = textInfos.ControlField(
			{
				"IAccessible::role": str(oleacc.ROLE_SYSTEM_PUSHBUTTON),
				"IAccessible2::attribute_tag": "dt",
				"IAccessible2::attribute_xml-roles": "button",
				"name": "Button label",
				"nameIsDuplicate": "true",
			},
		)
		Gecko_ia2_TextInfo.__new__(Gecko_ia2_TextInfo)._normalizeControlField(field)
		self.assertEqual(controlTypes.Role.BUTTON, field["role"])
		self.assertEqual("Button label", field["name"])

	def test_nativeCountNormalization(self) -> None:
		for textInfoClass, tagAttribute, tag in (
			(Gecko_ia2_TextInfo, "IAccessible2::attribute_tag", "dt"),
			(MSHTMLTextInfo, "IHTMLDOMNode::nodeName", "DT"),
		):
			for count in (0, 1, 2, 5):
				with self.subTest(backend=textInfoClass, count=count):
					info = textInfoClass.__new__(textInfoClass)
					field = textInfos.ControlField(
						{
							"IAccessible::role": str(oleacc.ROLE_SYSTEM_LISTITEM),
							tagAttribute: tag,
							"definition-count": str(count),
						},
					)
					info._normalizeControlField(field)
					self.assertEqual(controlTypes.Role.TERM, field["role"])
					self.assertEqual(count, field["definition-count"])

	def test_nativeListGroupCount(self) -> None:
		for textInfoClass, tagAttribute, tag in (
			(Gecko_ia2_TextInfo, "IAccessible2::attribute_tag", "dl"),
			(MSHTMLTextInfo, "IHTMLDOMNode::nodeName", "DL"),
		):
			with self.subTest(backend=textInfoClass):
				info = textInfoClass.__new__(textInfoClass)
				field = textInfos.ControlField(
					{
						"IAccessible::role": str(oleacc.ROLE_SYSTEM_LIST),
						tagAttribute: tag,
						"description-list-group-count": "2",
						"_childcontrolcount": "7",
					},
				)
				info._normalizeControlField(field)
				self.assertEqual(controlTypes.Role.DESCRIPTIONLIST, field["role"])
				self.assertEqual(2, int(field["_childcontrolcount"]))


class TestDescriptionListPresentation(unittest.TestCase):
	def setUp(self) -> None:
		self.formatConfig = config.conf["documentFormatting"].copy()
		self.formatConfig["reportLists"] = True

	def test_speechCountWhenEnteringTerm(self) -> None:
		for reason in (OutputReason.CARET, OutputReason.SAYALL, OutputReason.QUICKNAV, OutputReason.FOCUS):
			for count in (None, 0, 1, 2, 5):
				with self.subTest(reason=reason, count=count):
					field = textInfos.ControlField(role=controlTypes.Role.TERM)
					if count is not None:
						field["definition-count"] = count
					# Quick navigation/focus report marker roles after their content.
					fieldType = (
						"end_relative"
						if reason in (OutputReason.QUICKNAV, OutputReason.FOCUS)
						else "start_relative"
					)
					sequence = getControlFieldSpeech(field, [], fieldType, self.formatConfig, reason=reason)
					actual = [item for item in sequence if isinstance(item, str) and item]
					expected = ["term"]
					if count is not None and count > 1:
						expected.append(f"with {count} definitions")
					self.assertEqual(expected, actual)

	def test_speechDoesNotRepeatCountWithinTermOrOnExit(self) -> None:
		field = textInfos.ControlField(role=controlTypes.Role.TERM, **{"definition-count": 3})
		for fieldType in ("start_inControlFieldStack", "end_relative", "end_removedFromControlFieldStack"):
			with self.subTest(fieldType=fieldType):
				self.assertFalse(
					getControlFieldSpeech(field, [], fieldType, self.formatConfig, reason=OutputReason.CARET),
				)

	def test_brailleCount(self) -> None:
		for count in (None, 0, 1, 2, 5):
			with self.subTest(count=count):
				field = textInfos.ControlField(role=controlTypes.Role.TERM)
				if count is not None:
					field["definition-count"] = count
				actual = getControlFieldBraille(None, field, [], True, self.formatConfig)
				self.assertEqual(f"trm {count} defs" if count is not None and count > 1 else "trm", actual)
				self.assertIsNone(getControlFieldBraille(None, field, [], False, self.formatConfig))

	def test_brailleListAcceptsNumericGroupCount(self) -> None:
		for role, label in ((controlTypes.Role.LIST, "lst"), (controlTypes.Role.DESCRIPTIONLIST, "dlst")):
			for count in (2, "2"):
				with self.subTest(role=role, count=count):
					field = textInfos.ControlField(role=role, _childcontrolcount=count, _startOfNode=True)
					self.assertEqual(
						f"{label}2",
						getControlFieldBraille(None, field, [], True, self.formatConfig),
					)

	def test_descriptionListContainerPresentation(self) -> None:
		for reason in (OutputReason.CARET, OutputReason.SAYALL, OutputReason.QUICKNAV, OutputReason.FOCUS):
			for states in (set(), {controlTypes.State.READONLY}):
				with self.subTest(reason=reason, states=states):
					field = textInfos.ControlField(
						role=controlTypes.Role.DESCRIPTIONLIST,
						states=states,
						_childcontrolcount=2,
						_startOfNode=True,
						_endOfNode=True,
					)
					self.assertEqual(
						field.PRESCAT_CONTAINER,
						field.getPresentationCategory([], self.formatConfig, reason=reason),
					)
					for fieldType, expected in (
						("start_addedToControlFieldStack", ["description list", "with 2 items"]),
						("end_removedFromControlFieldStack", ["out of description list"]),
					):
						self.assertEqual(
							expected,
							[
								item
								for item in getControlFieldSpeech(
									field,
									[],
									fieldType,
									self.formatConfig,
									reason=reason,
								)
								if item
							],
						)
					self.assertEqual(
						"dlst end",
						getControlFieldBraille(None, field, [], False, self.formatConfig),
					)
					self.formatConfig["reportLists"] = False
					self.assertFalse(
						getControlFieldSpeech(
							field,
							[],
							"start_addedToControlFieldStack",
							self.formatConfig,
							reason=reason,
						),
					)
					self.assertFalse(getControlFieldBraille(None, field, [], True, self.formatConfig))
					self.formatConfig["reportLists"] = True

	def test_reportListsOffSuppressesRolesAndCounts(self) -> None:
		self.formatConfig["reportLists"] = False
		field = textInfos.ControlField(role=controlTypes.Role.TERM, **{"definition-count": 3})
		self.assertFalse(
			getControlFieldSpeech(field, [], "start_relative", self.formatConfig, reason=OutputReason.CARET),
		)
		self.assertFalse(getControlFieldBraille(None, field, [], True, self.formatConfig))

	def test_countDoesNotAffectOtherRoles(self) -> None:
		for role in (controlTypes.Role.DEFINITION, controlTypes.Role.LISTITEM, controlTypes.Role.BUTTON):
			with self.subTest(role=role):
				field = textInfos.ControlField(role=role)
				expectedSpeech = getControlFieldSpeech(
					field,
					[],
					"start_relative",
					self.formatConfig,
					reason=OutputReason.CARET,
				)
				expectedBraille = getControlFieldBraille(None, field, [], True, self.formatConfig)
				field["definition-count"] = 3
				self.assertEqual(
					expectedSpeech,
					getControlFieldSpeech(
						field,
						[],
						"start_relative",
						self.formatConfig,
						reason=OutputReason.CARET,
					),
				)
				self.assertEqual(
					expectedBraille,
					getControlFieldBraille(None, field, [], True, self.formatConfig),
				)

	def test_customRoleDescriptionsKeepCount(self) -> None:
		field = textInfos.ControlField(
			role=controlTypes.Role.TERM,
			roleText="entry",
			roleTextBraille="ent",
			**{"definition-count": 2},
		)
		self.assertEqual(
			["entry", "with 2 definitions"],
			[
				item
				for item in getControlFieldSpeech(
					field,
					[],
					"start_relative",
					self.formatConfig,
					reason=OutputReason.CARET,
				)
				if item
			],
		)
		self.assertEqual("ent 2 defs", getControlFieldBraille(None, field, [], True, self.formatConfig))
