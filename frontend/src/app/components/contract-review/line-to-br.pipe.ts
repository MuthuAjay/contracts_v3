import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';

@Pipe({
  name: 'lineToBr',
  standalone: true
})
export class LineToBrPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(value: string): SafeHtml {
    if (!value) return '';
    
    try {
      // Use marked to handle the markdown conversion
      const html = marked.parse(value, { async: false }) as string;
      return this.sanitizer.bypassSecurityTrustHtml(html);
    } catch (err) {
      console.error('Error parsing markdown:', err);
      
      // Fallback to original implementation if marked fails
      let processed = value
        // Transform markdown bullets (- item) to HTML
        .replace(/^-\s+(.+)$/gm, '<li>$1</li>')
        // Transform markdown bullets (* item) to HTML
        .replace(/^\*\s+(.+)$/gm, '<li>$1</li>')
        // Transform markdown sub-bullets (  - item) to HTML with proper indentation
        .replace(/^(\s{2,})-\s+(.+)$/gm, '<li class="nested">$2</li>')
        // Transform markdown sub-bullets (  * item) to HTML with proper indentation
        .replace(/^(\s{2,})\*\s+(.+)$/gm, '<li class="nested">$2</li>')
        // Transform numbered lists (1. item)
        .replace(/^(\d+)\.\s+(.+)$/gm, '<li class="numbered">$2</li>');
      
      // Wrap sequences of <li> elements with <ul>
      processed = processed.replace(/((?:<li.*?>.*?<\/li>)+)/g, '<ul>$1</ul>');
      
      // Handle headings
      processed = processed
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^#### (.+)$/gm, '<h4>$1</h4>');
        
      // Handle bold and italic
      processed = processed
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        .replace(/\_\_(.+?)\_\_/g, '<strong>$1</strong>')
        .replace(/\_(.+?)\_/g, '<em>$1</em>');
      
      // Handle code blocks
      processed = processed
        .replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>');
      
      // Replace newlines with <br> tags for remaining text
      processed = processed.replace(/\n/g, '<br>');
      
      return this.sanitizer.bypassSecurityTrustHtml(processed);
    }
  }
}