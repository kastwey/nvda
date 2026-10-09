# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later, as modified by the NVDA license.
# For full terms and any additional permissions, see the NVDA license file: https://github.com/nvaccess/nvda/blob/master/copying.txt

"""Chromium UIA and native web provider description-list regressions."""

import unittest  # noqa: I001
from types import SimpleNamespace
from unittest.mock import Mock, patch

import IAccessibleHandler  # noqa: F401 - Initialize before importing IAccessible object modules.
import config
import controlTypes
import oleacc
import textInfos
from braille.regions.properties import getControlFieldBraille
from comInterfaces import IAccessible2Lib as IA2
from NVDAObjects.IAccessible import IAccessible
from NVDAObjects.IAccessible.ia2Web import Ia2Web
from NVDAObjects.IAccessible.MSHTML import MSHTML as MSHTMLObject
from NVDAObjects.UIA import chromium
from speech.speech import getControlFieldSpeech
from virtualBuffers.gecko_ia2 import Gecko_ia2, Gecko_ia2_TextInfo
from virtualBuffers.MSHTML import MSHTML, MSHTMLTextInfo


class _Element:
	def __init__(self, role: str, children: list["_Element"] | None = None) -> None:
		self.role = role
		self.children = children or []
		self.cacheUpdates = 0

	def getCurrentPropertyValue(self, _propertyId: int) -> str:
		return self.role

	def getRuntimeId(self) -> tuple[int, ...]:
		return (id(self),)

	def buildUpdatedCache(self, request: object) -> "_Element":
		self.cacheUpdates += 1
		return self

	def getCachedChildren(self) -> SimpleNamespace:
		return SimpleNamespace(length=len(self.children), getElement=self.children.__getitem__)

	def getCachedPropertyValue(self, propertyId: int) -> str | tuple[int, ...]:
		if propertyId == chromium.UIAHandler.UIA_RuntimeIdPropertyId:
			return self.getRuntimeId()
		return self.role


def _fieldCommands(*fields: textInfos.ControlField) -> list[textInfos.FieldCommand | str]:
	return [
		*(textInfos.FieldCommand("controlStart", field) for field in fields),
		"content",
		*(textInfos.FieldCommand("controlEnd", None) for _ in fields),
	]


def _listElement(*roles: str) -> _Element:
	return _Element("list", [_Element(role) for role in roles])


class TestDescriptionListGroupCount(unittest.TestCase):
	def setUp(self) -> None:
		self.client = Mock()
		self.handlerPatch = patch.object(
			chromium.UIAHandler,
			"handler",
			SimpleNamespace(clientObject=self.client),
		)
		self.handlerPatch.start()
		self.addCleanup(self.handlerPatch.stop)

	def test_groupCounts(self) -> None:
		self.assertEqual("term", chromium._getPrimaryAriaRole("unsupported term"))
		self.assertEqual("button", chromium._getPrimaryAriaRole("button term"))
		testCases = (
			("ordinary list", _listElement("listitem", "listitem"), None),
			("empty list", _listElement(), None),
			("terms without definitions", _listElement("term", "term"), None),
			(
				"ordinary list with group",
				_Element("list", [_Element("group", [_Element("listitem")])]),
				None,
			),
			(
				"many-to-many direct groups",
				_listElement(
					"listitem",
					"definition",
					"listitem",
					"listitem",
					"definition",
					"definition",
				),
				2,
			),
			(
				"direct div wrappers",
				_Element(
					"list",
					[
						_Element("group", [_Element("listitem"), _Element("definition")]),
						_Element(
							"group",
							[_Element("listitem"), _Element("listitem"), _Element("definition")],
						),
					],
				),
				2,
			),
			(
				"mixed direct and wrapped groups",
				_Element("list", [_Element("listitem"), _Element("group", [_Element("definition")])]),
				1,
			),
			(
				"fallback roles",
				_listElement("unsupported listitem", "unsupported definition"),
				1,
			),
			(
				"valid role override",
				_listElement("button term", "button definition"),
				None,
			),
			(
				"nested div wrapper",
				_Element(
					"list",
					[_Element("group", [_Element("group", [_Element("term"), _Element("definition")])])],
				),
				None,
			),
			(
				"unpaired trailing term",
				_listElement("listitem", "definition", "listitem"),
				1,
			),
			("definition without term", _listElement("definition"), 0),
		)
		for description, listElement, expectedCount in testCases:
			with self.subTest(description=description):
				info = chromium._getDescriptionListInfo(listElement)
				self.assertEqual(expectedCount, info.groupCount if info is not None else None)

	def test_nestedDescriptionListIsIndependent(self) -> None:
		innerList = _Element("list", [_Element("listitem"), _Element("definition")])
		outerList = _Element(
			"list",
			[
				_Element("listitem"),
				_Element("definition", [innerList]),
			],
		)

		self.assertEqual(1, chromium._getDescriptionListInfo(outerList).groupCount)
		self.assertEqual(1, chromium._getDescriptionListInfo(innerList).groupCount)
		ordinaryList = _Element("list", [_Element("listitem", [innerList])])
		self.assertIsNone(chromium._getDescriptionListInfo(ordinaryList))

	def test_containerRoleOverrides(self) -> None:
		for role in ("button", "group", "listbox", "directory", "unsupported listbox list"):
			with self.subTest(role=role):
				listElement = _Element(role, [_Element("term"), _Element("definition")])
				self.assertIsNone(chromium._getDescriptionListInfo(listElement))
				self.assertEqual(0, listElement.cacheUpdates)
		self.client.createCacheRequest.assert_not_called()
		self.assertEqual(
			1,
			chromium._getDescriptionListInfo(
				_Element("unsupported list", [_Element("term"), _Element("definition")]),
			).groupCount,
		)

	def test_containerFieldNormalization(self) -> None:
		for ariaRole, children, expectedRole in (
			("list", ["listitem", "definition"], controlTypes.Role.DESCRIPTIONLIST),
			("list", ["listitem", "listitem"], controlTypes.Role.LIST),
			("listbox", ["term", "definition"], controlTypes.Role.LIST),
			("directory", ["term", "definition"], controlTypes.Role.LIST),
		):
			with self.subTest(ariaRole=ariaRole, children=children):
				obj = SimpleNamespace(
					role=controlTypes.Role.LIST,
					UIAElement=_Element(ariaRole, [_Element(role) for role in children]),
				)
				field = textInfos.ControlField(
					role=controlTypes.Role.LIST,
					states={controlTypes.State.READONLY},
					_childcontrolcount=7,
				)
				info = chromium.ChromiumUIATextInfo.__new__(chromium.ChromiumUIATextInfo)
				with patch.object(
					chromium.web.UIAWebTextInfo,
					"_getControlFieldForUIAObject",
					return_value=field,
				):
					self.assertIs(field, info._getControlFieldForUIAObject(obj))
				self.assertEqual(expectedRole, field["role"])
				self.assertEqual({controlTypes.State.READONLY}, field["states"])
				if expectedRole == controlTypes.Role.DESCRIPTIONLIST:
					self.assertEqual(1, field["_childcontrolcount"])
					term = textInfos.ControlField(
						role=controlTypes.Role.LISTITEM,
						runtimeID=obj.UIAElement.children[0].getRuntimeId(),
					)
					chromium._normalizeDescriptionListTerms(_fieldCommands(field, term))
					self.assertEqual(controlTypes.Role.TERM, term["role"])
					self.assertEqual(1, term["definition-count"])
				else:
					self.assertEqual(7, field["_childcontrolcount"])
				self.assertNotIn("_descriptionListInfo", field)

	def test_definitionCounts(self) -> None:
		for wrap in (False, True):
			with self.subTest(wrap=wrap):
				first, synonym, second, orphan = (_Element("term") for _ in range(4))
				groups = [
					[first, synonym, _Element("definition"), _Element("definition")],
					[second, _Element("definition", [_listElement("term", "definition", "definition")])],
					[orphan],
				]
				children = (
					[_Element("group", group) for group in groups]
					if wrap
					else [child for group in groups for child in group]
				)
				info = chromium._getDescriptionListInfo(_Element("list", children))
				self.assertEqual(2, info.groupCount)
				self.assertEqual(
					{
						first.getRuntimeId(): 2,
						synonym.getRuntimeId(): 2,
						second.getRuntimeId(): 1,
						orphan.getRuntimeId(): 0,
					},
					info.definitionCounts,
				)

	def test_groupSpansWrappers(self) -> None:
		"""Definitions in adjacent wrappers share the preceding term."""
		term = _Element("term")
		listElement = _Element(
			"list",
			[
				_Element("definition"),
				_Element("group", [term, _Element("definition")]),
				_Element("group", [_Element("definition")]),
			],
		)
		info = chromium._getDescriptionListInfo(listElement)
		self.assertEqual(1, info.groupCount)
		self.assertEqual({term.getRuntimeId(): 2}, info.definitionCounts)

	def test_definitionParagraphsAreNotSeparateDefinitions(self) -> None:
		term = _Element("listitem", [_Element("description")])
		paragraphs = [_Element("group", [_Element("description")]) for _ in range(2)]
		listElement = _Element(
			"list",
			[term, _Element("definition", paragraphs), _Element("definition")],
		)
		info = chromium._getDescriptionListInfo(listElement)
		self.assertEqual(1, info.groupCount)
		self.assertEqual({term.getRuntimeId(): 2}, info.definitionCounts)
		# Chromium's "description" role identifies static text, not a dd container.
		self.assertIsNone(chromium._getDescriptionListInfo(_listElement("listitem", "description")))

	def test_comFailureDiscardsPartialCounts(self) -> None:
		for obj, method in (
			(_Element, "getCachedChildren"),
			(_Element, "getCachedPropertyValue"),
			(self.client, "createCacheRequest"),
		):
			with (
				self.subTest(method=method),
				patch.object(obj, method, side_effect=chromium.COMError(-2147467259, "Failed", None)),
			):
				self.assertIsNone(chromium._getDescriptionListInfo(_listElement("term", "definition")))

	def test_largeListUsesOneRawViewSnapshot(self) -> None:
		listElement = _listElement(*(["term", "definition"] * 1000))
		with patch.object(_Element, "getCurrentPropertyValue", return_value="list") as currentProperty:
			info = chromium._getDescriptionListInfo(listElement)
		self.assertEqual(1000, info.groupCount)
		self.assertEqual(1, listElement.cacheUpdates)
		self.assertTrue(all(child.cacheUpdates == 0 for child in listElement.children))
		currentProperty.assert_not_called()
		self.assertIn(
			chromium.UIAHandler.UIA_AriaRolePropertyId,
			chromium.ChromiumUIATextInfo._controlFieldUIACachedPropertyIDs,
		)
		request = self.client.createCacheRequest.return_value
		self.assertEqual(chromium.UIAHandler.TreeScope_Children, request.treeScope)
		self.assertIs(self.client.RawViewCondition, request.treeFilter)
		self.assertEqual(
			[chromium.UIAHandler.UIA_AriaRolePropertyId, chromium.UIAHandler.UIA_RuntimeIdPropertyId],
			[call.args[0] for call in request.addProperty.call_args_list],
		)

	def test_countsAreRecomputedAfterChange(self) -> None:
		term = _Element("term")
		listElement = _Element("list")
		for count in (2, 3, 1):
			listElement.children = [term, *(_Element("definition") for _ in range(count))]
			info = chromium._getDescriptionListInfo(listElement)
			self.assertEqual(count, info.definitionCounts[term.getRuntimeId()])
		self.assertEqual(3, listElement.cacheUpdates)


class TestNormalizeDescriptionListTerms(unittest.TestCase):
	def test_deepFieldsUseLinearRoleLookups(self) -> None:
		groups = [textInfos.ControlField(role=controlTypes.Role.GROUPING) for _ in range(500)]
		term = textInfos.ControlField(role=controlTypes.Role.LISTITEM, runtimeID=(1,))
		fields = _fieldCommands(
			textInfos.ControlField(
				role=controlTypes.Role.DESCRIPTIONLIST,
				_descriptionListInfo=chromium._DescriptionListInfo(1, {(1,): 2}),
			),
			*groups,
			term,
		)
		lookups = 0

		def countedGet(field: textInfos.ControlField, key: str, default: object = None) -> object:
			nonlocal lookups
			lookups += 1
			return dict.get(field, key, default)

		with patch.object(textInfos.ControlField, "get", countedGet):
			chromium._normalizeDescriptionListTerms(fields)
		self.assertEqual(controlTypes.Role.TERM, term["role"])
		self.assertEqual(2, term["definition-count"])
		# Count work instead of timing, so the regression is independent of machine speed.
		self.assertLessEqual(lookups, len(groups) + 4)

	def test_ordinaryListItemIsUnchanged(self) -> None:
		listField = textInfos.ControlField(role=controlTypes.Role.LIST)
		itemField = textInfos.ControlField(role=controlTypes.Role.LISTITEM, name="Item")
		fields = _fieldCommands(listField, itemField)

		chromium._normalizeDescriptionListTerms(fields)

		self.assertEqual(controlTypes.Role.LISTITEM, itemField["role"])
		self.assertEqual("Item", itemField["name"])

	def test_roleNormalizationPreservesNames(self) -> None:
		for initialRole in (controlTypes.Role.LISTITEM, controlTypes.Role.TERM):
			with self.subTest(initialRole=initialRole):
				listField = textInfos.ControlField(
					role=controlTypes.Role.DESCRIPTIONLIST,
					_descriptionListInfo=chromium._DescriptionListInfo(),
				)
				itemField = textInfos.ControlField(role=initialRole, name="Term", alwaysReportName=True)
				fields = _fieldCommands(listField, itemField)

				chromium._normalizeDescriptionListTerms(fields)

				self.assertEqual(controlTypes.Role.TERM, itemField["role"])
				self.assertEqual("Term", itemField["name"])
				self.assertTrue(itemField["alwaysReportName"])
				self.assertNotIn("_descriptionListInfo", listField)

	def test_nestedListsUseTheirOwnSemantics(self) -> None:
		descriptionListField = textInfos.ControlField(
			role=controlTypes.Role.DESCRIPTIONLIST,
			_descriptionListInfo=chromium._DescriptionListInfo(),
		)
		definitionField = textInfos.ControlField(role=controlTypes.Role.DEFINITION)
		ordinaryListField = textInfos.ControlField(role=controlTypes.Role.LIST)
		itemField = textInfos.ControlField(role=controlTypes.Role.LISTITEM, name="Nested item")
		ordinaryListFields = _fieldCommands(
			descriptionListField,
			definitionField,
			ordinaryListField,
			itemField,
		)
		chromium._normalizeDescriptionListTerms(ordinaryListFields)
		self.assertEqual(controlTypes.Role.LISTITEM, itemField["role"])
		self.assertEqual("Nested item", itemField["name"])

		outerListField = textInfos.ControlField(
			role=controlTypes.Role.DESCRIPTIONLIST,
			_descriptionListInfo=chromium._DescriptionListInfo(),
		)
		innerListField = textInfos.ControlField(
			role=controlTypes.Role.DESCRIPTIONLIST,
			_descriptionListInfo=chromium._DescriptionListInfo(),
		)
		innerItemField = textInfos.ControlField(role=controlTypes.Role.LISTITEM, name="Inner term")
		descriptionListFields = _fieldCommands(
			outerListField,
			definitionField,
			innerListField,
			innerItemField,
		)
		chromium._normalizeDescriptionListTerms(descriptionListFields)
		self.assertEqual(controlTypes.Role.TERM, innerItemField["role"])
		self.assertNotIn("_descriptionListInfo", outerListField)
		self.assertNotIn("_descriptionListInfo", innerListField)

	def test_partialRangeUsesFullGroupCounts(self) -> None:
		for role in (controlTypes.Role.LISTITEM, controlTypes.Role.TERM):
			with self.subTest(role=role):
				listField = textInfos.ControlField(
					role=controlTypes.Role.DESCRIPTIONLIST,
					_descriptionListInfo=chromium._DescriptionListInfo(1, {(1,): 3, (2,): 3}),
				)
				termField = textInfos.ControlField(role=role, runtimeID=(2,))
				# Only the second term is in the text range; all definitions are outside it.
				fields = _fieldCommands(listField, termField)
				chromium._normalizeDescriptionListTerms(fields)
				self.assertEqual(3, termField["definition-count"])
				self.assertNotIn("_descriptionListInfo", listField)

	def test_countsDoNotLeakIntoNestedLists(self) -> None:
		for innerInfo, expected in ((None, None), (chromium._DescriptionListInfo(1, {(2,): 2}), 2)):
			with self.subTest(expected=expected):
				outer = textInfos.ControlField(
					role=controlTypes.Role.DESCRIPTIONLIST,
					_descriptionListInfo=chromium._DescriptionListInfo(1, {(2,): 5}),
				)
				inner = textInfos.ControlField(
					role=controlTypes.Role.DESCRIPTIONLIST
					if innerInfo is not None
					else controlTypes.Role.LIST,
					_descriptionListInfo=innerInfo,
				)
				term = textInfos.ControlField(role=controlTypes.Role.LISTITEM, runtimeID=(2,))
				chromium._normalizeDescriptionListTerms(_fieldCommands(outer, inner, term))
				self.assertEqual(expected, term.get("definition-count"))
				# Leaving an inner list must restore the outer count for the next term.
				outer["_descriptionListInfo"] = chromium._DescriptionListInfo(1, {(2,): 5})
				inner["_descriptionListInfo"] = innerInfo
				followingTerm = textInfos.ControlField(role=controlTypes.Role.LISTITEM, runtimeID=(2,))
				fields = _fieldCommands(outer, inner, term)
				fields[-1:-1] = _fieldCommands(followingTerm)
				chromium._normalizeDescriptionListTerms(fields)
				self.assertEqual(5, followingTerm["definition-count"])

	def test_explicitItemRoleIsUnchanged(self) -> None:
		listField = textInfos.ControlField(
			role=controlTypes.Role.DESCRIPTIONLIST,
			_descriptionListInfo=chromium._DescriptionListInfo(1, {(1,): 2}),
		)
		itemField = textInfos.ControlField(role=controlTypes.Role.BUTTON, name="Button", runtimeID=(1,))
		chromium._normalizeDescriptionListTerms(_fieldCommands(listField, itemField))
		self.assertEqual(controlTypes.Role.BUTTON, itemField["role"])
		self.assertEqual("Button", itemField["name"])
		self.assertNotIn("definition-count", itemField)


class TestDescriptionListNames(unittest.TestCase):
	def setUp(self) -> None:
		self.textPattern = Mock()
		self.info = chromium.ChromiumUIATextInfo.__new__(chromium.ChromiumUIATextInfo)
		self.info._obj = Mock(return_value=SimpleNamespace(UIATextPattern=self.textPattern))

	def _getFields(
		self,
		role: controlTypes.Role,
		name: str,
		*,
		isDescriptionList: bool = True,
		content: str | None = None,
	) -> tuple[textInfos.ControlField, textInfos.TextInfo.TextWithFieldsT]:
		"""Build a field, then normalize a clipped reading range inside the full element."""
		field = textInfos.ControlField(role=role, name=name, states=set())
		if content is not None:
			field["content"] = content
		obj = SimpleNamespace(role=role, UIAElement=_Element("term"))
		with patch.object(chromium.web.UIAWebTextInfo, "_getControlFieldForUIAObject", return_value=field):
			self.info._getControlFieldForUIAObject(obj)
		listField = textInfos.ControlField(role=controlTypes.Role.LIST)
		if isDescriptionList:
			listField["_descriptionListInfo"] = chromium._DescriptionListInfo()
		fields = [
			textInfos.FieldCommand("controlStart", listField),
			textInfos.FieldCommand("controlStart", field),
			"Only part of the element is in this reading range",
			textInfos.FieldCommand("controlEnd", field),
			textInfos.FieldCommand("controlEnd", listField),
		]
		with patch.object(chromium.web.UIAWebTextInfo, "getTextWithFields", return_value=fields):
			result = self.info.getTextWithFields()
		self.assertNotIn("_descriptionListNameElement", field)
		return field, result

	def test_onlyDuplicateNamesAreRemoved(self) -> None:
		for role in (controlTypes.Role.LISTITEM, controlTypes.Role.TERM, controlTypes.Role.DEFINITION):
			for name, fullText, isDuplicate in (
				("Accessible label", "Visible text", False),
				("Same text", "Same text", True),
				("Same text", "  Same\ntext\t", True),
				("Label", "label", False),
				("Label", "", False),
				("Label", "\ufffc", False),
				("", "", False),
			):
				with self.subTest(role=role, name=name, fullText=fullText):
					self.textPattern.rangeFromChild.return_value.getText.return_value = fullText
					field, fields = self._getFields(role, name)
					if isDuplicate:
						self.assertNotIn("name", field)
						self.assertNotIn("alwaysReportName", field)
					else:
						self.assertEqual(name, field["name"])
						if name:
							self.assertTrue(field["alwaysReportName"])
					self.assertIn("Only part of the element is in this reading range", fields)

	def test_replacementContentIsPreserved(self) -> None:
		for role in (controlTypes.Role.LISTITEM, controlTypes.Role.TERM):
			for fullText in ("Visible text", "Accessible label"):
				with self.subTest(role=role, fullText=fullText):
					self.textPattern.rangeFromChild.return_value.getText.return_value = fullText
					field, _fields = self._getFields(role, "Accessible label", content="Accessible label")
					self.assertEqual("Accessible label", field["content"])

	def test_unrelatedNamesDoNotRequireTextQueries(self) -> None:
		for role in (controlTypes.Role.LISTITEM, controlTypes.Role.BUTTON, controlTypes.Role.GROUPING):
			with self.subTest(role=role):
				field, _fields = self._getFields(role, "Original name", isDescriptionList=False)
				self.assertEqual("Original name", field["name"])
				self.assertEqual(role, field["role"])
		self.textPattern.rangeFromChild.assert_not_called()

	def test_unavailableTextDoesNotDiscardName(self) -> None:
		self.textPattern.rangeFromChild.side_effect = chromium.COMError(-2147467259, "Failed", None)
		field, _fields = self._getFields(controlTypes.Role.LISTITEM, "Accessible label")
		self.assertEqual("Accessible label", field["name"])
		self.assertTrue(field["alwaysReportName"])

	def test_missingTextRangeDoesNotDiscardName(self) -> None:
		self.textPattern.rangeFromChild.return_value = None
		field, _fields = self._getFields(controlTypes.Role.TERM, "Accessible label")
		self.assertEqual("Accessible label", field["name"])

	def test_preservedNamesReachSpeechAndBraille(self) -> None:
		formatConfig = config.conf["documentFormatting"].copy()
		formatConfig["reportLists"] = True
		self.textPattern.rangeFromChild.return_value.getText.return_value = "Visible text"
		for role in (controlTypes.Role.LISTITEM, controlTypes.Role.TERM, controlTypes.Role.DEFINITION):
			with self.subTest(role=role):
				field, _fields = self._getFields(role, "Accessible label")
				for reason in (
					controlTypes.OutputReason.CARET,
					controlTypes.OutputReason.SAYALL,
					controlTypes.OutputReason.QUICKNAV,
				):
					fieldType = (
						"end_relative" if reason == controlTypes.OutputReason.QUICKNAV else "start_relative"
					)
					self.assertIn(
						"Accessible label",
						getControlFieldSpeech(field, [], fieldType, formatConfig, reason=reason),
					)
				self.assertIn("Accessible label", getControlFieldBraille(None, field, [], True, formatConfig))

	def test_webReplacementContentSurvivesFieldConstruction(self) -> None:
		for properties, text, expectedContent in (
			("label=Accessible label", "Visible text", "Accessible label"),
			("labelledby=label-id", "Visible text", "Accessible label"),
			("", "", "Accessible label"),
			("", "\ufffc", "Accessible label"),
			("", "Visible text", None),
		):
			with self.subTest(properties=properties, text=text):
				obj = SimpleNamespace(
					role=controlTypes.Role.TERM,
					UIAElement=SimpleNamespace(
						cachedControlType=chromium.UIAHandler.UIA_TextControlTypeId,
						getRuntimeId=lambda: (1,),
					),
					name="Accessible label",
					states=set(),
					description="",
					positionInfo={},
					landmark=None,
					isCurrent=controlTypes.IsCurrent.NO,
					placeholder=None,
					_getUIACacheablePropertyValue=Mock(return_value=properties),
				)
				self.info._obj.return_value.makeTextInfo = Mock(return_value=SimpleNamespace(text=text))
				field = self.info._getControlFieldForUIAObject(obj)
				self.assertEqual(expectedContent, field.get("content"))
				self.assertNotIn("name", field)
				self.assertNotIn("_descriptionListNameElement", field)


class TestNativeDescriptionListRoles(unittest.TestCase):
	def test_bufferRolesAndCounts(self) -> None:
		for textInfoClass, tagAttribute, roleAttribute in (
			(Gecko_ia2_TextInfo, "IAccessible2::attribute_tag", "IAccessible2::attribute_xml-roles"),
			(MSHTMLTextInfo, "IHTMLDOMNode::nodeName", "HTMLAttrib::role"),
		):
			for tag, ariaRole, nativeRole, expectedRole in (
				("dl", "", oleacc.ROLE_SYSTEM_LIST, controlTypes.Role.DESCRIPTIONLIST),
				("dl", "unsupported", oleacc.ROLE_SYSTEM_LIST, controlTypes.Role.DESCRIPTIONLIST),
				("dl", "list", oleacc.ROLE_SYSTEM_LIST, controlTypes.Role.LIST),
				("dl", "unsupported list", oleacc.ROLE_SYSTEM_LIST, controlTypes.Role.LIST),
				("dl", "unsupported\tlistbox", oleacc.ROLE_SYSTEM_LIST, controlTypes.Role.LIST),
				("dl", "listbox", oleacc.ROLE_SYSTEM_LIST, controlTypes.Role.LIST),
				("dl", "button list", oleacc.ROLE_SYSTEM_PUSHBUTTON, controlTypes.Role.BUTTON),
				("ul", "", oleacc.ROLE_SYSTEM_LIST, controlTypes.Role.LIST),
				("ol", "", oleacc.ROLE_SYSTEM_LIST, controlTypes.Role.LIST),
				("div", "term", IA2.IA2_ROLE_TEXT_FRAME, controlTypes.Role.TERM),
				("div", "unsupported term", IA2.IA2_ROLE_TEXT_FRAME, controlTypes.Role.TERM),
				("div", "button term", oleacc.ROLE_SYSTEM_PUSHBUTTON, controlTypes.Role.BUTTON),
			):
				with self.subTest(provider=textInfoClass, tag=tag, ariaRole=ariaRole):
					info = textInfoClass.__new__(textInfoClass)
					field = textInfos.ControlField(
						{
							"IAccessible::role": str(nativeRole),
							tagAttribute: tag.upper() if textInfoClass is MSHTMLTextInfo else tag,
							roleAttribute: ariaRole,
							"_childcontrolcount": "7",
						},
					)
					if tag == "dl":
						field["description-list-group-count"] = "2"
					info._normalizeControlField(field)
					self.assertEqual(expectedRole, field["role"])
					self.assertEqual(
						2 if expectedRole == controlTypes.Role.DESCRIPTIONLIST else 7,
						int(field["_childcontrolcount"]),
					)

	def test_ia2ObjectRoles(self) -> None:
		for tag, ariaRole, expectedRole in (
			("dl", "", controlTypes.Role.DESCRIPTIONLIST),
			("dl", "unsupported", controlTypes.Role.DESCRIPTIONLIST),
			("dl", "list", controlTypes.Role.LIST),
			("dl", "unsupported listbox", controlTypes.Role.LIST),
			("ul", "", controlTypes.Role.LIST),
			("ol", "", controlTypes.Role.LIST),
		):
			with (
				self.subTest(tag=tag, ariaRole=ariaRole),
				patch.object(IAccessible, "role", controlTypes.Role.LIST),
				patch.object(Ia2Web, "IA2Attributes", {"tag": tag, "xml-roles": ariaRole}),
			):
				obj = object.__new__(Ia2Web)
				self.assertEqual(expectedRole, obj._get_role())

	def test_mshtmlObjectRoles(self) -> None:
		for hasAncestor in (False, True):
			for ariaRole, expectedRole in (
				("", controlTypes.Role.DESCRIPTIONLIST),
				("unsupported", controlTypes.Role.DESCRIPTIONLIST),
				("list", controlTypes.Role.LIST),
				("unsupported list", controlTypes.Role.LIST),
				("button list", controlTypes.Role.BUTTON),
			):
				with (
					self.subTest(hasAncestor=hasAncestor, ariaRole=ariaRole),
					patch.multiple(
						MSHTMLObject,
						create=True,
						HTMLNode=True,
						HTMLAttributes={"role": ariaRole},
						HTMLNodeName="DL",
						HTMLNodeHasAncestorIAccessible=hasAncestor,
					),
				):
					obj = object.__new__(MSHTMLObject)
					self.assertEqual(expectedRole, obj._get_role())

	def test_mshtmlTermAndDefinitionObjectRoles(self) -> None:
		for hasAncestor in (False, True):
			for tag, nativeRole in (("DT", controlTypes.Role.TERM), ("DD", controlTypes.Role.DEFINITION)):
				for ariaRole, expected in (
					("", nativeRole),
					("unsupported", nativeRole),
					("button", controlTypes.Role.BUTTON),
				):
					with (
						self.subTest(hasAncestor=hasAncestor, tag=tag, ariaRole=ariaRole),
						patch.multiple(
							MSHTMLObject,
							create=True,
							HTMLNode=True,
							HTMLAttributes={"role": ariaRole},
							HTMLNodeName=tag,
							HTMLNodeHasAncestorIAccessible=hasAncestor,
						),
					):
						self.assertEqual(expected, object.__new__(MSHTMLObject)._get_role())

	def test_nativeListQuickNavIsUnchanged(self) -> None:
		self.assertEqual(
			{"IAccessible::role": [oleacc.ROLE_SYSTEM_LIST]},
			Gecko_ia2._searchableAttribsForNodeType(None, "list"),
		)
		self.assertEqual(
			{"IHTMLDOMNode::nodeName": ["UL", "OL", "DL"]},
			MSHTML._searchableAttribsForNodeType(None, "list"),
		)

	def test_mshtmlUnknownRoleDoesNotBecomeAnEditField(self) -> None:
		with (
			patch.object(IAccessible, "role", controlTypes.Role.EDITABLETEXT),
			patch.multiple(
				MSHTMLObject,
				create=True,
				HTMLNode=True,
				HTMLAttributes={"role": "unsupported"},
				HTMLNodeName="FUTURE-TAG",
				HTMLNodeHasAncestorIAccessible=False,
				IAccessibleChildID=0,
			),
		):
			self.assertEqual(controlTypes.Role.STATICTEXT, object.__new__(MSHTMLObject)._get_role())
