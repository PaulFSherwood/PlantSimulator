# Release Checklist

- [ ] `git status` is clean before release.
- [ ] `uvicorn app.main:app --reload` starts without traceback.
- [ ] `python3 scripts/smoke_check.py` passes.
- [ ] Dashboard updates live.
- [ ] Process Flow updates live.
- [ ] Equipment actions work.
- [ ] Alarms acknowledge.
- [ ] Scenario Builder starts scenarios.
- [ ] Reports export CSV.
- [ ] Login works with `owner / plantops`.
- [ ] Diagnostics page is OK.
- [ ] README and operations guide are current.
