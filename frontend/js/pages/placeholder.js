import { escapeHtml } from '../api.js';

export function renderPlaceholder(container, title, description) {
  container.innerHTML = `
    <div class="placeholder-page">
      <h1 class="page-title">${escapeHtml(title)}</h1>
      <p class="text-muted" style="margin-top: 1.5rem; font-size: 1.25rem">${escapeHtml(description)}</p>
      <a href="/" data-link>
        <button type="button" class="btn btn-primary btn-mt-lg">Back to Home</button>
      </a>
    </div>
  `;
}
