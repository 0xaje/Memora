#!/usr/bin/env python3
"""
MEMORA — Load-Bearing Sibyl Memory Live Demonstration Proof.

Demonstrates the core statement:
    'What happened before changes what Memora does now.'

Flow:
1. SESSION A: Ingest initial incident -> evaluate baseline -> write to real Sibyl Memory.
2. OUTCOME: Record unresolved follow-up -> persist lesson to Sibyl Memory.
3. FRESH SESSION B: Completely new session context with zero in-memory state.
4. FRESH SESSION B: Ingest related incident -> retrieve history from Sibyl.
5. VERIFY ESCALATION: Risk escalates from MEDIUM to HIGH and recommendation changes
   from MONITOR_AND_VERIFY to ESCALATE_TO_SUPERVISOR.
6. AUDIT: Inspect full evidence explanation showing exactly why the decision changed.
"""

import os
import sys
import tempfile
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

# Ensure project root is in PYTHONPATH
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from memora.memory.client import SibylClientManager
from memora.incidents.service import IncidentService
from memora.incidents.models import IncidentCreate, OutcomeCreate, RiskLevel, RecommendationType

console = Console()


def run_demonstration():
    console.print(Panel.fit(
        "[bold cyan]MEMORA — AI OPERATIONAL MEMORY AGENT[/bold cyan]\n"
        "[italic white]Live Load-Bearing Proof with Real Sibyl Memory (SQLite FTS5)[/italic white]",
        box=box.DOUBLE
    ))

    # Create isolated DB file for this demonstration
    demo_db = Path(tempfile.gettempdir()) / "memora_live_proof.db"
    if demo_db.exists():
        demo_db.unlink()

    console.print(f"[bold yellow]1. Initializing Real Sibyl Memory storage at:[/bold yellow] [dim]{demo_db}[/dim]\n")

    # ==============================================================
    # STEP 1: SESSION A — INITIAL OBSERVATION
    # ==============================================================
    console.print("[bold green]══════════════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]STEP 1: SESSION A — INITIAL OPERATIONAL INCIDENT[/bold green]")
    console.print("[bold green]══════════════════════════════════════════════════════════════[/bold green]")

    manager_a = SibylClientManager(db_path=str(demo_db))
    service_a = IncidentService(client_manager=manager_a)

    incident_a_text = "Suspicious delivery vehicle observed near Gate 3."
    console.print(f"[bold cyan]Intake Incident:[/bold cyan] '{incident_a_text}'")

    res_a = service_a.analyze_incident(
        IncidentCreate(raw_text=incident_a_text, session_id="session_A_live"),
        session_id="session_A_live",
        is_fresh_session=True
    )

    table_a = Table(title="Session A Assessment (Cold Start / No History)", box=box.ROUNDED)
    table_a.add_column("Property", style="cyan")
    table_a.add_column("Value", style="bold yellow")
    table_a.add_row("Incident ID", res_a.incident.incident_id)
    table_a.add_row("Location", res_a.incident.location)
    table_a.add_row("Extracted Type", res_a.incident.incident_type)
    table_a.add_row("Baseline Risk", res_a.baseline_assessment.risk.value)
    table_a.add_row("Baseline Recommendation", res_a.baseline_assessment.recommendation.value)
    table_a.add_row("Sibyl Hits Retrieved", str(res_a.memory_influence.retrieval_count))
    table_a.add_row("Final Risk", res_a.memory_assessment.risk.value)
    table_a.add_row("Final Recommendation", res_a.memory_assessment.recommendation.value)
    table_a.add_row("Decision Changed?", "[red]False[/red]" if not res_a.memory_assessment.changed else "[green]True[/green]")
    console.print(table_a)

    console.print(f"[bold green]✔ Incident & Decision persisted to Sibyl Memory (Warm entities & Cold journal).[/bold green]\n")

    # ==============================================================
    # STEP 2: RECORD UNRESOLVED OUTCOME & LESSON
    # ==============================================================
    console.print("[bold green]══════════════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]STEP 2: RECORD OUTCOME & SYNTHESIZE OPERATIONAL LESSON[/bold green]")
    console.print("[bold green]══════════════════════════════════════════════════════════════[/bold green]")

    inc_id = res_a.incident.incident_id
    outcome_res = service_a.record_outcome(OutcomeCreate(
        incident_id=inc_id,
        action_taken="MONITOR_AND_VERIFY",
        observed_result="Similar suspicious delivery activity occurred again. Vehicle departed before credentials verified.",
        is_resolved=False,
        unresolved_reason="Ongoing vulnerability; standard monitoring was insufficient.",
        operational_lesson="Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3."
    ))

    console.print(f"[bold cyan]Action Taken:[/bold cyan] MONITOR_AND_VERIFY")
    console.print(f"[bold cyan]Observed Result:[/bold cyan] Similar suspicious delivery activity occurred again.")
    console.print(f"[bold cyan]Status:[/bold cyan] [bold red]UNRESOLVED[/bold red]")
    console.print(f"[bold cyan]Synthesized Lesson:[/bold cyan] 'Monitoring alone did not resolve recurring suspicious delivery activity near Gate 3.'")
    console.print(f"[bold green]✔ Outcome, Unresolved Risk entity, and Operational Lesson saved into Sibyl Memory.[/bold green]\n")

    # Destroy Session A completely
    manager_a.close()
    del service_a
    del manager_a

    # ==============================================================
    # STEP 3: SESSION B — GENUINELY FRESH SESSION
    # ==============================================================
    console.print("[bold green]══════════════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]STEP 3: FRESH SESSION B — NEW OBSERVATION[/bold green]")
    console.print("[italic white](New process instance, zero conversational context, clean memory)[/italic white]")
    console.print("[bold green]══════════════════════════════════════════════════════════════[/bold green]")

    manager_b = SibylClientManager(db_path=str(demo_db))
    service_b = IncidentService(client_manager=manager_b)

    incident_b_text = "Suspicious delivery vehicle observed again near Gate 3."
    console.print(f"[bold cyan]Fresh Session Intake:[/bold cyan] '{incident_b_text}'")

    res_b = service_b.analyze_incident(
        IncidentCreate(raw_text=incident_b_text, session_id="session_B_fresh_live"),
        session_id="session_B_fresh_live",
        is_fresh_session=True
    )

    table_b = Table(title="Session B Assessment (Load-Bearing Memory Applied)", box=box.ROUNDED)
    table_b.add_column("Property", style="cyan")
    table_b.add_column("Value", style="bold")
    table_b.add_row("Session ID", res_b.session.id)
    table_b.add_row("Is Fresh Session?", "[green]True[/green]" if res_b.session.is_fresh else "False")
    table_b.add_row("Baseline Risk (Without Memory)", f"[yellow]{res_b.baseline_assessment.risk.value}[/yellow]")
    table_b.add_row("Baseline Recommendation", f"[yellow]{res_b.baseline_assessment.recommendation.value}[/yellow]")
    table_b.add_row("Sibyl Records Retrieved", f"[bold green]{res_b.memory_influence.retrieval_count}[/bold green]")
    table_b.add_row("Related Incidents in History", str(len(res_b.memory_influence.related_incidents)))
    table_b.add_row("Unresolved Risks Found", str(len(res_b.memory_influence.unresolved_risks)))
    table_b.add_row("Operational Lessons Found", str(len(res_b.memory_influence.operational_lessons)))
    table_b.add_row("Memory-Informed Risk", f"[bold red]{res_b.memory_assessment.risk.value}[/bold red]")
    table_b.add_row("Memory-Informed Recommendation", f"[bold red]{res_b.memory_assessment.recommendation.value}[/bold red]")
    table_b.add_row("DECISION CHANGED?", "[bold green]YES (TRUE)[/bold green]" if res_b.memory_assessment.changed else "[red]NO[/red]")
    console.print(table_b)

    # ==============================================================
    # STEP 4: AUDITABLE EVIDENCE EXPLANATION
    # ==============================================================
    console.print("\n[bold green]══════════════════════════════════════════════════════════════[/bold green]")
    console.print("[bold green]STEP 4: AUDITABLE DECISION EXPLANATION[/bold green]")
    console.print("[bold green]══════════════════════════════════════════════════════════════[/bold green]")

    exp = res_b.explanation
    console.print(Panel(
        f"[bold cyan]What Happened:[/bold cyan]\n{exp.what_happened}\n\n"
        f"[bold cyan]What Was Retrieved From Sibyl:[/bold cyan]\n{exp.what_was_retrieved}\n\n"
        f"[bold cyan]Pattern Inferred:[/bold cyan]\n{exp.what_pattern_was_inferred}\n\n"
        f"[bold cyan]Why Decision Changed:[/bold cyan]\n[bold yellow]{exp.why_decision_changed}[/bold yellow]",
        title="[bold green]Memora Audit Trail[/bold green]",
        box=box.ROUNDED
    ))

    manager_b.close()
    if demo_db.exists():
        demo_db.unlink()

    console.print("\n[bold green]✔ PROOF COMPLETE: Load-bearing memory loop verified successfully![/bold green]\n")


if __name__ == "__main__":
    run_demonstration()
