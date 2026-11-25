from __future__ import annotations

"""Beihang Referee as an MCP server: Referee directs, YOUR AI reviews.

Connect this server to any MCP-capable assistant (Claude, ChatGPT connectors,
Cursor, local clients). The assistant does the reading and writing with its own
model, so Referee needs no API key. Referee supplies the workflow, the rules,
and deterministic checks the assistant cannot fake: exact-quote verification,
numerical and reference checks, passage retrieval, a concern admission gate, a
graded editorial decision, and a frozen ledger for revision rounds.

Start with `get_playbook`, then `start_review`.
"""

from typing import Any


def build_server():
    try:  # mcp 1.x
        from mcp.server.fastmcp import FastMCP
    except ImportError:
        try:  # mcp 2.x renamed FastMCP to MCPServer
            from mcp.server.mcpserver import MCPServer as FastMCP
        except ImportError as exc:
            raise RuntimeError("MCP support requires the optional `mcp` package: pip install mcp") from exc
    from .. import direction as D
    from ..ingestion import PackageInspector
    from ..comparison import revision_diff, audit_rebuttal_structure
    from ..documents import DocumentLoader
    from ..modes import ReviewModeRegistry

    mcp = FastMCP("Beihang Referee")

    @mcp.tool()
    def get_playbook(stage: str | None = None) -> dict:
        """START HERE. With no argument: the phased workflow plus the DISCOVER rules only (evidence, defect hunt, coverage). Call again with 'adjudicate', 'write' or 'revise' when you reach those phases, or with one rule name (phases, evidence, defect_hunt, coverage, decision, stopping, voice, report_style, elevation, writing, response). Style and decision rules are deliberately withheld during discovery so they cannot compete with finding defects."""
        return D.playbook(stage)

    @mcp.tool()
    def start_review(path: str | None = None, text: str | None = None) -> dict:
        """Load a manuscript (file path: pdf, docx, md, txt, tex) or pasted text. Returns a manuscript_id used by the other tools, the opening text, and the playbook."""
        return D.start_review(path, text)

    @mcp.tool()
    def find_passages(manuscript_id: str, query: str, k: int = 5) -> dict:
        """Retrieve the passages of the manuscript most relevant to a query (BM25). Use it to locate evidence before raising a concern."""
        return D.find_passages(D.Session.load(manuscript_id), query, k)

    @mcp.tool()
    def verify_quote(manuscript_id: str, quote: str) -> dict:
        """Check that a quote really appears in the manuscript (whitespace/case tolerant). Every concern anchor must pass this. Returns verified or not_found."""
        return D.verify_quote(D.Session.load(manuscript_id), quote)

    @mcp.tool()
    def check_numbers(manuscript_id: str) -> dict:
        """Offline recomputation: reported test statistics vs p-values (t, F, chi2, r, z), GRIM on means, counts vs percentages, citation numbering, duplicate DOIs. Objective facts to cite."""
        return D.check_numbers(D.Session.load(manuscript_id))

    @mcp.tool()
    def check_references(manuscript_id: str) -> dict:
        """Verify cited DOIs against Crossref (existence, retraction notices, title match) and list possible uncited prior art from Europe PMC. Needs internet, no key."""
        return D.check_references(D.Session.load(manuscript_id))

    @mcp.tool()
    def check_writing(manuscript_id: str) -> dict:
        """Descriptive prose metrics (sentence length, hedging, passive voice, acronyms never defined) plus flags a careful editor would raise. Descriptive, not a quality score."""
        return D.check_writing_tool(D.Session.load(manuscript_id))

    @mcp.tool()
    def audit_response(response_text: str, reviewer_comments_text: str | None = None) -> dict:
        """Audit an author's response-to-reviewers letter against Noble's ten simple rules (overview, quoted reviews, direct answers, self-contained changes, no bare 'addressed in the manuscript', tone flags, every point answered). Reports which comments look unanswered."""
        from ..response import audit_response as _audit
        return _audit(response_text, reviewer_comments_text)

    @mcp.tool()
    def response_skeleton(reviewer_comments_text: str, title: str = "the manuscript") -> str:
        """Turn reviewer comments into an interleaved response-to-reviewers template (author side)."""
        from ..response import response_skeleton as _sk
        return _sk(reviewer_comments_text, title)

    @mcp.tool()
    def provenance_log(manuscript_id: str) -> list[dict[str, Any]]:
        """Append-only record of which Referee tools ran on this manuscript, when, and a summary of each result."""
        return D.provenance(manuscript_id)

    @mcp.tool()
    def check_figures(pdf_path: str) -> dict:
        """Find duplicated or re-used images inside a PDF's figures (perceptual hashing, flips, rotations, quadrants). Findings mean 'a human should compare these two images', never proof of misconduct. Needs pymupdf and pillow."""
        from ..verification.figures import check_figures as _cf
        return _cf(pdf_path)

    @mcp.tool()
    def trace_claim(manuscript_id: str, claim_text: str, k: int = 4) -> dict:
        """Follow a claim to its result passages and method passages, with the questions to ask about how the number was produced. Use for every central claim."""
        return D.trace_claim(D.Session.load(manuscript_id), claim_text, k)

    @mcp.tool()
    def inspect_code(path: str) -> dict:
        """Attention pointers for a supplied Python file: lag/shift/alignment operations, a lag set once and reused across participants, preprocessing before a train/test split, unseeded splits. Pointers are places to read, not verdicts."""
        return D.inspect_code(open(path, encoding="utf-8", errors="replace").read(), path)

    @mcp.tool()
    def submit_concerns(manuscript_id: str, claims: list[dict[str, Any]], concerns: list[dict[str, Any]],
                        require_verification: bool = False, independent_verdicts: dict[str, dict[str, Any]] | None = None) -> dict:
        """The admission gate and decision. claims: [{claim_id, text, centrality: central|supporting}]. concerns: [{title, claim_ids, anchors:[exact quotes, or {quote, shows}], failure_mechanism, scientific_consequence, consequence_level: invalidates|changes_interpretation|weakens|minor, fix_type: wording|reanalysis|new_data, minimum_resolution, closure_criterion, confidence 0-1, steelman, survives_steelman: true, steelman_survival}]. Checks: quotes exist AND relate to the concern; confidence valid; the concern survives its steelman; near-duplicates merge; budget by central claim. STRONGEST MODE: call with require_verification=true to get verification packets, give them to a second AI context, then call again with independent_verdicts {packet_id: verdict}. Without it the result is marked verification_level self_only (provisional). The ledger is frozen and cannot be overwritten."""
        return D.submit_concerns(D.Session.load(manuscript_id), claims, concerns, 1, independent_verdicts, require_verification)

    @mcp.tool()
    def lint_review(review_text: str, gate_result: dict[str, Any], max_words: int = 3500) -> dict:
        """After writing the review, check it against the gate result: length budget, the gate's recommendation, every admitted concern present (information loss), no extra major comments, no repetition or fragmentation. gate_result is the return value of submit_concerns."""
        return D.lint_review(review_text, gate_result, max_words)

    @mcp.tool()
    def revision_round(new_manuscript_id: str, prior_manuscript_id: str, statuses: dict[str, dict[str, Any]],
                       new_concerns: list[dict[str, Any]] | None = None) -> dict:
        """Judge a revised manuscript against the FROZEN, hash-checked ledger of the previous round. statuses: {concern_id: {status: OPEN|PARTIAL|VERIFIED_CLOSED|WORSENED, evidence_quote: exact quote from the CHANGED text that addresses the closure criterion (required to close; text that already existed in the first version cannot close unless unchanged_text_justification is given), note}}. new_concerns need origin introduced_by_revision, missed_factual_error, or field_development (then also external_source: DOI/URL), with anchors in the revised text; anything else is rejected as moving the goalposts."""
        return D.revision_round(D.Session.load(new_manuscript_id), prior_manuscript_id, statuses, new_concerns)

    @mcp.tool()
    def inspect_package(paths: list[str]) -> dict:
        """Inspect manuscript/reproducibility package structure without running a model."""
        return PackageInspector().inspect(paths).to_dict()

    @mcp.tool()
    def compare_revision(old_path: str, new_path: str) -> dict:
        """Compare two manuscript versions structurally."""
        loader = DocumentLoader()
        return revision_diff(loader.load(old_path).text, loader.load(new_path).text)

    @mcp.tool()
    def audit_rebuttal(response_path: str) -> dict:
        """Audit reviewer-response traceability signals."""
        return audit_rebuttal_structure(DocumentLoader().load(response_path).text)

    @mcp.tool()
    def list_review_modes() -> list[str]:
        """List supported review purposes."""
        return ReviewModeRegistry().names()

    return mcp


def main():
    build_server().run()


if __name__ == "__main__":
    main()
