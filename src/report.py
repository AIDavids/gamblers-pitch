"""
report.py - a tiny helper that builds the checkpoint report text file.

Each stage writes reports/checkpoint_N.txt. You paste that ONE file back to
Claude instead of screenshots or long tables. Only plain ASCII characters are
used so it also prints correctly in the Windows command prompt.
"""
from datetime import datetime


class Report:
    def __init__(self, title):
        self.lines = [title, "Run time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ""]
        self.checks = []          # list of (status, name, detail)

    def line(self, text=""):
        self.lines.append(str(text))

    def section(self, title):
        self.lines.append("")
        self.lines.append("=== " + title + " ===")

    def table(self, df, max_rows=60):
        """Add a pandas table (limited to max_rows so reports stay short)."""
        if len(df) > max_rows:
            self.lines.append(df.head(max_rows).to_string())
            self.lines.append("... (%d more rows not shown)" % (len(df) - max_rows))
        else:
            self.lines.append(df.to_string())

    def check(self, name, status, detail=""):
        """status is PASS, FAIL or WARN. FAIL means: stop and ask (spec rule 8)."""
        assert status in ("PASS", "FAIL", "WARN")
        self.checks.append((status, name, detail))

    def n_failed(self):
        return sum(1 for s, _, _ in self.checks if s == "FAIL")

    def finish(self):
        self.section("AUTO-CHECKS")
        for status, name, detail in self.checks:
            tail = ("  -> " + detail) if detail else ""
            self.lines.append("[%s] %s%s" % (status, name, tail))
        n_pass = sum(1 for s, _, _ in self.checks if s == "PASS")
        n_warn = sum(1 for s, _, _ in self.checks if s == "WARN")
        self.lines.append("")
        self.lines.append("SUMMARY: %d passed, %d warnings, %d failed" % (n_pass, n_warn, self.n_failed()))
        return "\n".join(self.lines)

    def save(self, path):
        text = self.finish()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return text
