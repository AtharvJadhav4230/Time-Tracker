### Summary
<!-- Provide a brief description of the changes introduced by this pull request. -->

Closes #199

### Validation Evidence
<!-- Fill out the table below detailing author-run checks. CI runs do not replace local validation. -->
<!-- For documentation-only changes, mention 'N/A - Doc change' and describe your manual walkthrough. -->

| Environment (OS / Python) | Command or Manual Step Run | Actual Result | Reason if Skipped |
| :--- | :--- | :--- | :--- |
| e.g., Windows 11 / Python 3.11 | `.\venv\Scripts\python.exe -m unittest discover -v` | All tests passed | |
| e.g., Ubuntu / Python 3.10 | `./venv/bin/python -m unittest discover -v` | All tests passed | |
| Documentation walkthrough | Markdown preview & link verification | Formatted cleanly, links valid | |

### Checklist
- [ ] Linked issue referenced in the summary
- [ ] Local validation performed and evidence table filled above
- [ ] Preserved user privacy (no PII, local secrets, or tracking telemetry introduced)
- [ ] If changing interface/installer: UI and installation flows manually verified (or marked N/A)