*** Settings ***
Documentation	Reproduce container-end navigation with an external static page.
Library	NvdaLib.py
Library	ChromeLib.py
Library	containerNavigationTests.py
Test Setup	start NVDA	standard-dontShowWelcomeDialog.ini
Test Teardown	clean up

*** Keywords ***
clean up
	Run Keyword And Ignore Error	dump_speech_to_log
	Run Keyword And Ignore Error	dump_braille_to_log
	Run Keyword And Ignore Error	close_chrome_tab
	quit NVDA

*** Test Cases ***
Move past lists with IA2
	[Tags]	container_reproduction
	test_container_navigation	${False}

Move past lists with UIA
	[Tags]	container_reproduction
	test_container_navigation	${True}