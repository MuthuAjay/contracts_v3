import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { LineToBrPipe } from '../contract-review/line-to-br.pipe';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { Router } from '@angular/router';
import { MarkdownToHtmlPipe } from './legal-research.pipe';
import { DomSanitizer } from '@angular/platform-browser';

@Component({
  selector: 'app-legal-research',
  templateUrl: './legal-research.component.html',
  styleUrl: './legal-research.component.scss',
  imports: [
      CommonModule,
      MatCardModule,
      MatDividerModule,
      MatProgressSpinnerModule,
      MatIconModule,
      MatTooltipModule,
      MatExpansionModule,
      MatButtonModule,
      LineToBrPipe,
      MarkdownToHtmlPipe
  ],
  standalone: true
})
export class LegalResearchComponent implements OnInit {
  contractData: any = null;
  isLoading = true;
  currentSection = 'all';
  fileName: string = '';
  analysisType: string = '';
  analysisDate: Date | null = null;
  rawData: any = null; // Store raw data for debugging

  constructor(private router: Router, private sanitizer: DomSanitizer) {}
  
  ngOnInit() {
    this.loadContractData();
  }

  // Return to contracts list
  backToContracts() {
    this.router.navigate(['/Contract']);
  }

  getSections(): string[] {
    if (!this.contractData) return [];
    return Object.keys(this.contractData).filter(key => 
      this.contractData![key] && typeof this.contractData![key] === 'string' && this.contractData![key].trim() !== ''
    );
  }

  async loadContractData() {
    try {
      // Get data from localStorage
      const currentAnalysis = localStorage.getItem('legal_research');
      console.log("Legal research data:", currentAnalysis);
      
      if (currentAnalysis) {
        const analysisData = JSON.parse(currentAnalysis);
        this.rawData = analysisData; // Store for debugging
        this.fileName = analysisData.fileName || 'Unknown File';
        this.analysisType = analysisData.type || 'Legal Research';
        this.analysisDate = analysisData.analysisDate ? new Date(analysisData.analysisDate) : new Date();
        
        // Format the data
        if (analysisData.result) {
          // Direct access to Legal Research content
          let legalResearch = analysisData.result['Legal Research'];
          
          // Check what we're dealing with
          console.log("Legal Research type:", typeof legalResearch);
          
          if (typeof legalResearch === 'string') {
            // It's a string, use directly
            this.contractData = {
              'Research Results': this.sanitizer.bypassSecurityTrustHtml(marked.parse(legalResearch, { async: false }) as string)
            };
          } else if (typeof legalResearch === 'object') {
            // It's an object, process each key
            const formattedData: any = {};
            
            Object.keys(legalResearch).forEach(key => {
              const content = legalResearch[key];
              if (typeof content === 'string' && content.trim() !== '') {
                try {
                  const html = marked.parse(content, { async: false }) as string;
                  formattedData[key] = this.sanitizer.bypassSecurityTrustHtml(html);
                } catch (err) {
                  console.error(`Error parsing markdown for ${key}:`, err);
                  formattedData[key] = content; // Use raw if parsing fails
                }
              }
            });
            
            this.contractData = formattedData;
          }
        }
        
        console.log('Formatted Legal Research Data:', this.contractData);
      }
    } catch (error) {
      console.error('Error loading legal research data:', error);
      // Show raw data if parsing fails
      const currentAnalysis = localStorage.getItem('legal_research');
      if (currentAnalysis) {
        try {
          const data = JSON.parse(currentAnalysis);
          if (data.result && data.result['Legal Research']) {
            this.contractData = {
              'Raw Data': data.result['Legal Research']
            };
          }
        } catch (e) {
          console.error('Failed to display raw data:', e);
        }
      }
    } finally {
      this.isLoading = false;
    }
  }
}

// Import marked for direct use in the component
import { marked } from 'marked';

// Configure marked options for better list handling
marked.setOptions({
  breaks: true,
  gfm: true
});
