# A part of NonVisual Desktop Access (NVDA)
# This file is covered by the GNU General Public License.
# See the file COPYING for more details.
# Copyright (C) 2020-2026 NV Access limited, Leonard de Ruijter


from comtypes import COMError  # noqa: I001

from dataclasses import dataclass, field

import aria
import UIAHandler
from . import web
import controlTypes
import textInfos
from UIAHandler.browseMode import UIAControlQuicknavIterator

"""
This module provides UIA behaviour specific to the chromium family of browsers.
Note this is more specialised than UIA.web but less so than browser specific modules such as UIA.spartan_edge
or UIA.anaheim_edge.
"""


def _getPrimaryAriaRole(ariaRoles: object) -> str | None:
	"""Return the first recognized role from a UIA AriaRole fallback list."""
	if not isinstance(ariaRoles, str):
		return None
	return next(
		(role for role in ariaRoles.lower().split() if role in aria.ariaRolesToNVDARoles),
		None,
	)


@dataclass
class _DescriptionListInfo:
	"""Counts from the full list tree, including definitions outside the current text range."""

	groupCount: int = 0
	definitionCounts: dict[tuple[int, ...], int] = field(default_factory=dict)


def _getDescriptionListInfo(
	listElement: UIAHandler.IUIAutomationElement,
) -> _DescriptionListInfo | None:
	"""Count groups and associate each term with all definitions in its group.

	Chromium exposes native description-list terms as ``listitem`` and definitions
	as ``definition`` in the raw view. The control view can omit definitions and
	expose their paragraphs instead, so it cannot provide association counts.
	HTML also permits one level of direct ``div`` wrappers, exposed as ``group``
	when retained in the accessibility tree.
	UIA does not distinguish a native ``dl`` from an explicit ``role="list"``
	with the same descendants. Empty lists and lists with no exposed definitions
	therefore retain their ordinary list semantics.
	The element must include the AriaRole property cached for control fields.
	"""
	info = _DescriptionListInfo()
	hasDefinitions = False
	terms: list[tuple[int, ...]] = []
	definitionCount = 0

	def finishGroup() -> None:
		nonlocal definitionCount
		if terms and definitionCount:
			info.groupCount += 1
		for term in terms:
			info.definitionCounts[term] = definitionCount
		terms.clear()
		definitionCount = 0

	def processChildren(
		parentElement: UIAHandler.IUIAutomationElement,
		allowGroupWrappers: bool,
	) -> None:
		nonlocal hasDefinitions, definitionCount
		children = parentElement.buildUpdatedCache(cacheRequest).getCachedChildren()
		if not children:
			return
		for index in range(children.length):
			child = children.getElement(index)
			ariaRole = _getPrimaryAriaRole(
				child.getCachedPropertyValue(UIAHandler.UIA_AriaRolePropertyId),
			)
			if ariaRole in ("listitem", "term"):
				if definitionCount:
					finishGroup()
				terms.append(tuple(child.getCachedPropertyValue(UIAHandler.UIA_RuntimeIdPropertyId)))
			elif ariaRole == "definition":
				hasDefinitions = True
				definitionCount += 1
			elif allowGroupWrappers and ariaRole == "group":
				processChildren(child, False)

	try:
		# Native dl and ordinary lists both expose "list". Other recognized
		# roles (including listbox/directory) must retain their explicit semantics.
		if _getPrimaryAriaRole(
			listElement.getCachedPropertyValue(UIAHandler.UIA_AriaRolePropertyId),
		) not in (None, "list"):
			return None
		clientObject = UIAHandler.handler.clientObject
		# Fetch each level in one cache request, rather than making cross-process
		# calls for every sibling, role and runtime ID. Do not retain this snapshot
		# between reads: DOM changes must update the counts immediately.
		cacheRequest = clientObject.createCacheRequest()
		cacheRequest.treeScope = UIAHandler.TreeScope_Children
		cacheRequest.treeFilter = clientObject.RawViewCondition
		cacheRequest.addProperty(UIAHandler.UIA_AriaRolePropertyId)
		cacheRequest.addProperty(UIAHandler.UIA_RuntimeIdPropertyId)
		processChildren(listElement, True)
	except COMError:
		return None
	finishGroup()
	return info if hasDefinitions else None


def _normalizeDescriptionListTerms(fields: textInfos.TextInfo.TextWithFieldsT) -> None:
	"""Normalize terms using their nearest list's full-tree association counts."""
	# Inherit the nearest list at each level rather than repeatedly searching ancestors.
	controlFieldStack: list[_DescriptionListInfo | None] = []
	for item in fields:
		if not isinstance(item, textInfos.FieldCommand):
			continue
		if item.command == "controlStart":
			listInfo = item.field.pop("_descriptionListInfo", None)
			nearestListInfo = controlFieldStack[-1] if controlFieldStack else None
			role = item.field.get("role")
			if role == controlTypes.Role.TERM or (
				role == controlTypes.Role.LISTITEM and nearestListInfo is not None
			):
				item.field["role"] = controlTypes.Role.TERM
				if nearestListInfo is not None:
					runtimeID = tuple(item.field.get("runtimeID", ()))
					if runtimeID in nearestListInfo.definitionCounts:
						item.field["definition-count"] = nearestListInfo.definitionCounts[runtimeID]
			controlFieldStack.append(
				listInfo
				if role in (controlTypes.Role.LIST, controlTypes.Role.DESCRIPTIONLIST)
				else nearestListInfo,
			)
		elif item.command == "controlEnd" and controlFieldStack:
			controlFieldStack.pop()


class ChromiumUIATextInfo(web.UIAWebTextInfo):
	def expand(self, unit):
		# #12474: Expanding to line breaks when the underlying text range is empty.
		if (
			UIAHandler.NVDAUnitsToUIAUnits.get(unit) == UIAHandler.UIA.TextUnit_Line
			and self.obj.UIATextPattern.documentRange.GetText(1) == ""
		):
			return
		super().expand(unit)

	def _getFormatFieldAtRange(self, textRange, formatConfig, ignoreMixedValues=False):
		formatField = super()._getFormatFieldAtRange(
			textRange,
			formatConfig,
			ignoreMixedValues=ignoreMixedValues,
		)
		# Headings are also exposed in the element tree,
		# And therefore exposing in a formatField is redundant and causes duplicate reporting.
		# So remove heading-level from the formatField if it exists.
		try:
			del formatField.field["heading-level"]
		except KeyError:
			pass
		return formatField

	def _getControlFieldForUIAObject(self, obj, isEmbedded=False, startOfNode=False, endOfNode=False):
		field = super()._getControlFieldForUIAObject(
			obj,
			isEmbedded=isEmbedded,
			startOfNode=startOfNode,
			endOfNode=endOfNode,
		)
		# use the value of comboboxes as content.
		if obj.role == controlTypes.Role.COMBOBOX:
			field["content"] = obj.value
		# Layout tables do not have the UIA table pattern
		if field["role"] == controlTypes.Role.TABLE:  # noqa: SIM102
			if not obj._getUIACacheablePropertyValue(UIAHandler.UIA_IsTablePatternAvailablePropertyId):
				field["table-layout"] = True
		if obj.role == controlTypes.Role.LIST:
			listInfo = _getDescriptionListInfo(obj.UIAElement)
			if listInfo is not None:
				# Normalize the text field, not the object role: role lookups must not
				# traverse the entire UIA tree or interfere with list overlay selection.
				field["role"] = controlTypes.Role.DESCRIPTIONLIST
				field["_descriptionListInfo"] = listInfo
				field["_childcontrolcount"] = listInfo.groupCount
		if field.get("name") and field["role"] in (
			controlTypes.Role.LISTITEM,
			controlTypes.Role.TERM,
			controlTypes.Role.DEFINITION,
		):
			# List items are only identifiable as terms after their ancestors are normalized.
			# Keep the element until then, without querying text for ordinary list items.
			field["_descriptionListNameElement"] = obj.UIAElement
		# Currently no way to tell if author has explicitly set name.
		# Therefore always report the name if the control is not of a type that
		# by definition uses its name for content.
		# this may cause some duplicate speaking,
		# But that is currently better than nothing at all.
		if not field.get("nameIsContent") and field.get("name"):
			field["alwaysReportName"] = True
		return field

	def _removeDuplicateDescriptionListNames(self, fields: textInfos.TextInfo.TextWithFieldsT) -> None:
		"""Suppress names only when they duplicate the complete term or definition text."""
		for item in fields:
			if not isinstance(item, textInfos.FieldCommand) or item.command != "controlStart":
				continue
			field = item.field
			element = field.pop("_descriptionListNameElement", None)
			if element is None or field["role"] not in (controlTypes.Role.TERM, controlTypes.Role.DEFINITION):
				continue
			try:
				# The reading range can cover only part of the element, so do not compare
				# with the strings in fields. Chromium need not expose the label's origin.
				textRange = self.obj.UIATextPattern.rangeFromChild(element)
				text = textRange.getText(-1) if textRange else None
			except COMError:
				# Inability to prove duplication must not discard an accessible name.
				continue
			if text is not None and field["name"].split() == text.split():
				field.pop("name", None)
				field.pop("alwaysReportName", None)

	def getTextWithFields(
		self,
		formatConfig: dict | None = None,
	) -> textInfos.TextInfo.TextWithFieldsT:
		fields = super().getTextWithFields(formatConfig)
		_normalizeDescriptionListTerms(fields)
		self._removeDuplicateDescriptionListNames(fields)
		return fields


class ChromiumUIA(web.UIAWeb):
	_TextInfo = ChromiumUIATextInfo

	def _get_states(self) -> set[controlTypes.State]:
		states = super().states
		if self.role == controlTypes.Role.LINK and self.linkType:
			states.add(self.linkType)
		return states


class ChromiumUIATreeInterceptor(web.UIAWebTreeInterceptor):
	def _iterNodesByType(self, nodeType, direction="next", pos=None):
		if nodeType == "listItem":
			clientObject = UIAHandler.handler.clientObject
			condition = clientObject.createOrCondition(
				clientObject.createPropertyCondition(
					UIAHandler.UIA_ControlTypePropertyId,
					UIAHandler.UIA_ListItemControlTypeId,
				),
				clientObject.createPropertyCondition(
					UIAHandler.UIA_AriaRolePropertyId,
					"term",
				),
			)
			return UIAControlQuicknavIterator(nodeType, self, pos, condition, direction)
		return super()._iterNodesByType(nodeType, direction=direction, pos=pos)

	def _get_documentConstantIdentifier(self):
		return self.rootNVDAObject.parent._getUIACacheablePropertyValue(UIAHandler.UIA_AutomationIdPropertyId)

	def _get_documentURL(self) -> str | None:
		return self.rootNVDAObject.value


class ChromiumUIADocument(ChromiumUIA):
	treeInterceptorClass = ChromiumUIATreeInterceptor

	def _get_shouldCreateTreeInterceptor(self):
		return self.role == controlTypes.Role.DOCUMENT
