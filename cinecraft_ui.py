"""CineCraft.AI — presentation HTML builders for the notebook UI.

Pure, stateless helpers that return HTML strings for the notebook's richer
visual cards. Keeping these here strips a lot of inline HTML/CSS out of the
notebook so the code cells stay focused on logic.

The notebook remains responsible for calling `display(HTML(...))`.
"""
from __future__ import annotations


def movie_intel_card_html(refs: list[dict]) -> str:
    """Render the recalled reference films as a clean bulleted card (chips)."""
    chips = "".join(
        f"<li style='display:flex;align-items:center;gap:8px;padding:6px 0;"
        f"border-top:1px solid #f1f5f9;list-style:none;'>"
        f"<span style='color:#f59e0b;'>🎬</span><span>{m['title']}</span></li>"
        for m in refs)
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;width:100%;box-sizing:border-box;
                border:1px solid #fde68a;border-radius:14px;overflow:hidden;margin:10px 0;
                box-shadow:0 4px 14px rgba(245,158,11,.12);">
      <div style="background:linear-gradient(135deg,#f59e0b,#f97316);padding:10px 16px;color:#fff;">
        <span style="font-size:14px;font-weight:700;">🎞️ MovieIntel — {len(refs)} reference films recalled</span>
      </div>
      <ul style="padding:10px 16px;margin:0;font-size:13px;color:#111827;line-height:1.5;">{chips}</ul>
    </div>
    """


# The <style> block that constrains the native input() textbox so it stays a
# sensible width and never stretches full-width (which pushes a horizontal
# scrollbar) across the many notebook/Jupyter/VS Code stdin widget variants.
STDIN_INPUT_STYLE = """
<style>
  .cell-output input[type="text"],
  .cell-output-ipywidget-background input,
  .output input[type="text"],
  .jp-OutputArea input[type="text"],
  .jp-Stdin-input,
  .jupyter-widgets input[type="text"],
  .widget-text input,
  .nb-stdin input,
  .cell-output-stdin input,
  .stdin-widget input,
  .interactive-input-box input,
  .monaco-inputbox input,
  .monaco-inputbox textarea,
  .output_stdin input {
      max-width: 420px !important;
      width: 420px !important;
      min-width: 0 !important;
      box-sizing: border-box !important;
      flex: 0 1 420px !important;
  }
  .nb-stdin,
  .cell-output-stdin,
  .stdin-widget,
  .interactive-input-box,
  .monaco-inputbox,
  .jp-Stdin {
      max-width: 460px !important;
      width: 460px !important;
      min-width: 0 !important;
      flex: 0 0 auto !important;
      box-sizing: border-box !important;
  }
</style>
"""


def select_direction_chips_html(opts: list[dict]) -> str:
    """Render the numbered creative-direction option chips for the gate card."""
    return "".join(
        f"""<div style="display:flex;gap:12px;align-items:flex-start;padding:12px 14px;margin:8px 0;
                    border:1px solid #eef0f3;border-radius:12px;background:#fafafe;">
              <div style="flex:0 0 30px;height:30px;border-radius:50%;background:#6366f1;color:#fff;
                          display:flex;align-items:center;justify-content:center;font-weight:700;">{i}</div>
              <div><div style="font-weight:600;">{d['name']}</div>
                   <div style="color:#4b5563;font-size:13px;margin-top:2px;">{d['rationale']}</div></div>
            </div>"""
        for i, d in enumerate(opts))


def launch_banner_html() -> str:
    """The 'Continuing from the Week-1 Saga Summary' launch banner."""
    return """
<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;width:100%;
            box-sizing:border-box;border-radius:16px;overflow:hidden;
            box-shadow:0 8px 24px rgba(0,0,0,.08);margin:12px 0;">
  <div style="background:linear-gradient(135deg,#8b5cf6,#6366f1);padding:16px 20px;color:#fff;">
    <div style="font-size:18px;font-weight:700;">🧠 Continuing from the Week-1 Saga Summary</div>
    <div style="font-size:13px;opacity:.9;margin-top:2px;">The whole Week-1 journey IS the premise — no re-pitch needed.</div>
  </div>
</div>
"""


def run_complete_summary_html(final_state: dict) -> str:
    """Build the completion-summary body (chosen direction / storyboards / scenes)."""
    chosen = final_state.get('chosen_direction', '—')
    n_boards = len(final_state.get('storyboards', []))
    n_scenes = len(final_state.get('production_plan', {}).get('scenes', []))
    return f"""
  <div style="display:flex;gap:24px;flex-wrap:wrap;">
    <div style="flex:1;min-width:180px;background:#f5f3ff;border-radius:12px;padding:14px 16px;">
      <div style="font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.5px;">Chosen Direction</div>
      <div style="font-size:16px;font-weight:700;margin-top:4px;">{chosen}</div>
    </div>
    <div style="flex:1;min-width:120px;background:#ecfeff;border-radius:12px;padding:14px 16px;">
      <div style="font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.5px;">Storyboards</div>
      <div style="font-size:16px;font-weight:700;margin-top:4px;">{n_boards} 🖼️</div>
    </div>
    <div style="flex:1;min-width:120px;background:#f0fdf4;border-radius:12px;padding:14px 16px;">
      <div style="font-size:12px;color:#6b7280;text-transform:uppercase;letter-spacing:.5px;">Planned Scenes</div>
      <div style="font-size:16px;font-weight:700;margin-top:4px;">{n_scenes} 🎬</div>
    </div>
  </div>
"""
