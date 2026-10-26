# TomoClub website

## SEO Real URLs project

For any SEO Real URLs work:

- **Start of session:** read `docs/seo-real-urls/00-context.md` and `docs/seo-real-urls/STATUS.md` before you do anything. STATUS.md tells you the current phase, step and next action.
- **After every completed step:** run the `seo-checkpoint` skill. Do not wait until the end of the phase. Do not finish a response that completed a step without updating STATUS.md.
- **When a decision is made:** add it to the decision log in STATUS.md in the same response.
- **Approval:** never set a phase to `approved` yourself. Only Rohith approves. When a phase is `waiting for review`, stop.
- **Next phase:** when Rohith approves a phase, run the `seo-next` skill.
- **Source of truth:** STATUS.md for progress and decisions. `00-context.md` for goal, architecture and plan. If two files disagree, tell Rohith. Do not decide alone.
- **Real-world setup:** when a step needs people, devices or sessions, do not ask open "can you do X?" questions. List every requirement for the best result. Rohith says which are not possible, and we agree compromises.

# Session Wrap-Up

When the user says **"end the session"** or **"wrap up this session"**: record a summary of all changes, updates, decisions made, and bugs encountered/fixed during the session into `memory.md`, each entry stamped with a timestamp. Append — don't overwrite prior entries.
