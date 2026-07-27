/** Map validated presentation presets to fixed CSS classes (never inject CSS). */

const PRESET_CLASS = {
  young_reader: 'adaptive-message--young',
  middle_reader: 'adaptive-message--middle',
  advanced_reader: 'adaptive-message--advanced',
};

/**
 * @param {object|null|undefined} presentation
 * @returns {string} space-separated class names
 */
export function adaptiveMessageClass(presentation) {
  if (!presentation || typeof presentation !== 'object') {
    return 'adaptive-message adaptive-message--middle';
  }

  const presetClass = PRESET_CLASS[presentation.preset] || 'adaptive-message--middle';
  const parts = ['adaptive-message', presetClass];

  if (presentation.font_style === 'rounded' || presentation.fontStyle === 'rounded') {
    parts.push('adaptive-message--rounded');
  }
  if (presentation.font_scale === 'large' || presentation.fontScale === 'large') {
    parts.push('adaptive-message--scale-large');
  } else if (presentation.font_scale === 'compact' || presentation.fontScale === 'compact') {
    parts.push('adaptive-message--scale-compact');
  } else {
    parts.push('adaptive-message--scale-medium');
  }

  if (presentation.line_spacing === 'relaxed' || presentation.lineSpacing === 'relaxed') {
    parts.push('adaptive-message--spacing-relaxed');
  } else {
    parts.push('adaptive-message--spacing-normal');
  }

  const width = presentation.content_width || presentation.contentWidth;
  if (width === 'narrow') parts.push('adaptive-message--width-narrow');
  else if (width === 'wide') parts.push('adaptive-message--width-wide');
  else parts.push('adaptive-message--width-medium');

  const emphasis = presentation.emphasis_style || presentation.emphasisStyle;
  if (emphasis === 'keywords') parts.push('adaptive-message--emphasis-keywords');

  return parts.join(' ');
}
