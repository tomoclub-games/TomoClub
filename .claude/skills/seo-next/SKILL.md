---
name: seo-next
description: Start the next phase of SEO Real URLs after Rohith approves the current one. Use when Rohith says a phase is approved, says "next phase", or asks what to do next on SEO Real URLs.
---

# Start the next SEO Real URLs phase

1. **Read** `docs/seo-real-urls/00-context.md` and `docs/seo-real-urls/STATUS.md`.
2. **Confirm approval:** the current phase must be approved by Rohith in this conversation or already marked `approved` in STATUS.md. If it is not, stop and ask.
3. **Close the phase:** set it to `approved` with Rohith's name and today's date. Move its checklist to "Completed phases" with a one-line result.
4. **Read the next phase** in "The plan" section of `00-context.md`. Use the outputs of the previous phase as input.
5. **Write the new checklist** in STATUS.md: small, concrete steps, each with a clear output. The first step is always "plan shown to Rohith and accepted". If the phase builds from a spec, add "spec approved by Rohith (**no code before this**)" before the build steps. The last step is always "summary given; phase set to `waiting for review`".
6. **Write the phase task spec:** add a new section to `00-context.md` named "Task spec: Phase X", in the same form as the Phase A spec. Log the change in the document change log.
7. **Show Rohith** the checklist and the plan, in plan mode. Do not implement anything until they accept.
