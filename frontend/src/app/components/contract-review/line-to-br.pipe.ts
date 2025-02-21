import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'lineToBr',
  standalone: true
})
export class LineToBrPipe implements PipeTransform {
  constructor(private sanitizer: DomSanitizer) {}

  transform(value: string): SafeHtml {
    if (!value) return '';
    
    // Replace newlines with <br> tags
    const withBrs = value.replace(/\n/g, '<br>');
    
    // Make numbered lists look better
    const withLists = withBrs.replace(/(\d+\.\s.*?)(<br>|$)/g, '<p class="list-item">$1</p>');
    
    // Check if content has HTML
    if (/<[a-z][\s\S]*>/i.test(withLists)) {
      // Content already has HTML
      return this.sanitizer.bypassSecurityTrustHtml(withLists);
    } else {
      // Plain text with formatting
      return this.sanitizer.bypassSecurityTrustHtml(withLists);
    }
  }
}