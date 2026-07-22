// Shared client-side utilities for PromptGuard.
// Page-specific logic lives in each template's {% block scripts %}.

document.addEventListener('DOMContentLoaded', () => {
  // Keyboard shortcut: Cmd/Ctrl+Enter submits the analyze form if present.
  const promptInput = document.getElementById('prompt-input');
  const analyzeBtn = document.getElementById('analyze-btn');
  if (promptInput && analyzeBtn) {
    promptInput.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        analyzeBtn.click();
      }
    });
  }
});
