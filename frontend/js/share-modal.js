function fallbackCopy(text) {
  const textarea = document.createElement('textarea');
  textarea.value = text;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'fixed';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();

  let copied;
  try {
	copied = document.execCommand('copy');
  } catch (err) {
	copied = false;
  }

  textarea.remove();
  return copied;
}

async function copyToClipboard(text) {
  if (navigator.clipboard?.writeText) {
	try {
	  await navigator.clipboard.writeText(text);
	  return true;
	} catch (err) {
	  return fallbackCopy(text);
	}
  }
  return fallbackCopy(text);
}

export function openShareModal(shareUrl, options = {}) {
  const { onCopyAndClose } = options;
  const previousOverflow = document.body.style.overflow;
  const previouslyFocused = document.activeElement;
  let closed = false;

  document.body.style.overflow = 'hidden';

  const overlay = document.createElement('div');
  overlay.className = 'share-modal-overlay';
  overlay.setAttribute('role', 'presentation');

  const dialog = document.createElement('div');
  dialog.className = 'share-modal';
  dialog.setAttribute('role', 'dialog');
  dialog.setAttribute('aria-modal', 'true');
  dialog.setAttribute('aria-labelledby', 'share-modal-title');
  dialog.tabIndex = -1;

  const title = document.createElement('p');
  title.className = 'share-modal-title';
  title.id = 'share-modal-title';
  title.textContent = 'Share this challenge with a friend:';

  const linkField = document.createElement('input');
  linkField.className = 'share-modal-link';
  linkField.type = 'text';
  linkField.readOnly = true;
  linkField.value = shareUrl;
  linkField.setAttribute('aria-label', 'Share link');

  const actions = document.createElement('div');
  actions.className = 'share-modal-actions';

  const copyAndCloseBtn = document.createElement('button');
  copyAndCloseBtn.type = 'button';
  copyAndCloseBtn.className = 'btn btn-primary';
  copyAndCloseBtn.textContent = 'Copy Link and Close';

  actions.appendChild(copyAndCloseBtn);
  dialog.append(title, linkField, actions);
  overlay.appendChild(dialog);

  function close() {
	if (closed) return;
	closed = true;
	document.removeEventListener('keydown', onKeyDown, true);
	document.body.style.overflow = previousOverflow;
	overlay.remove();
	if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
	  previouslyFocused.focus();
	}
  }

  function onKeyDown(e) {
	if (e.key === 'Escape') {
	  e.preventDefault();
	  close();
	}
  }

  overlay.addEventListener('click', (e) => {
	if (e.target === overlay) {
	  close();
	}
  });

  dialog.addEventListener('click', (e) => e.stopPropagation());

  copyAndCloseBtn.addEventListener('click', async () => {
	copyAndCloseBtn.disabled = true;
	try {
	  await copyToClipboard(shareUrl);
	} finally {
	  close();
      if (typeof onCopyAndClose === 'function') {
        onCopyAndClose();
      }
	}
  });

  document.addEventListener('keydown', onKeyDown, true);
  document.body.appendChild(overlay);
  dialog.focus();
}



