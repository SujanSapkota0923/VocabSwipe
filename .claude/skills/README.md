# Skills

A skill is a reusable instruction package: knowledge that more than one agent
needs, written once so it is applied the same way every time. Each skill lives
in its own folder, `.claude/skills/<name>/SKILL.md`, with a short frontmatter
(`name`, `description`) and the instructions.

None exist yet, on purpose. The agents in `.claude/agents/` and `CLAUDE.md`
already cover what VocabSwipe needs today. Add a skill only when the same
guidance has been repeated in several tasks or agents, for example:

- **Mobile UI checks** — the viewport list, safe areas, touch targets and the `tests/ui/` workflow, if UI tasks keep repeating them.
- **Django migrations** — how to write data-preserving migrations for the SQLite production disk, once model work starts (TASK-006, TASK-010).
- **Render deployment** — the pre-deploy and post-deploy checklist, if the deployer and developer both keep needing it.

Do not create a skill just because a technology is in the stack, and do not
copy content that already lives in `CLAUDE.md` or `docs/`.
