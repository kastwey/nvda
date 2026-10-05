# A part of NonVisual Desktop Access (NVDA)
# Copyright (C) 2026 NV Access Limited
# This file may be used under the terms of the GNU General Public License, version 2 or later.

*** Settings ***
Documentation   Real Gecko and MSHTML description-list tests; requires the selected host on Windows.
Library         NvdaLib.py
Library         descriptionListTests.py
Test Setup      Start NVDA    standard-dontShowWelcomeDialog.ini
Test Teardown   Finish Description List Test

*** Keywords ***
Finish Description List Test
    Run Keyword And Continue On Failure    Dump Speech To Log
    Run Keyword And Continue On Failure    Dump Braille To Log
    Run Keyword And Continue On Failure    Close Description List Host
    Quit NVDA

*** Test Cases ***
Firefox description list direct groups
    [Tags]    description_lists_firefox
    Check Description Lists    firefox    ${False}

Firefox description list wrapped groups
    [Tags]    description_lists_firefox
    Check Description Lists    firefox    ${True}

MSHTML description list direct groups
    [Tags]    description_lists_mshtml
    Check Description Lists    mshtml    ${False}

MSHTML description list wrapped groups
    [Tags]    description_lists_mshtml
    Check Description Lists    mshtml    ${True}