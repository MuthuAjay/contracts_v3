import { CommonModule } from '@angular/common';
import { Component, OnInit, AfterViewInit } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatExpansionModule } from '@angular/material/expansion';
import { Router } from '@angular/router';
import { LineToBrPipe } from './line-to-br.pipe';
import { marked } from 'marked';
import hljs from 'highlight.js';
import { RiskMarkdownPipe } from '../risk-assessment/risk-assessment.pipe';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { MatButtonModule } from '@angular/material/button';

// Configure minimal marked options that are safe in TypeScript
marked.setOptions({
  gfm: true,
  breaks: true
});

interface ContractData {
  'Contract Review'?: string | SafeHtml;
  'Key Terms'?: string | SafeHtml;
  'Obligations'?: string | SafeHtml;
  'Parties'?: string | SafeHtml;
  [key: string]: any; // Allow for dynamic properties
}

@Component({
  selector: 'app-contract-review',
  templateUrl: './contract-review.component.html',
  styleUrls: ['./contract-review.component.scss'],
  standalone: true,
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
    RiskMarkdownPipe
  ]
})
export class ContractReviewComponent implements OnInit, AfterViewInit {
  contractData: ContractData | null = null;
  isLoading = true;
  currentSection = 'all';
  fileName: string = '';
  analysisType: string = '';
  analysisDate: Date | null = null;
  rawData: any = null; // Store raw data for debugging
  
  // View mode properties
  viewMode: 'cards' | 'list' | 'compact' = 'cards';

  constructor(private router: Router, private sanitizer: DomSanitizer) {}

  ngOnInit() {
    // Check if user has a saved view mode preference
    const savedViewMode = localStorage.getItem('contract_review_view_mode');
    if (savedViewMode && ['cards', 'list', 'compact'].includes(savedViewMode)) {
      this.viewMode = savedViewMode as 'cards' | 'list' | 'compact';
    }
    
    this.loadContractData();
  }

  // Add this method to your ContractReviewComponent class
  formatSectionId(section: string, prefix: string = 'section'): string {
    // First convert to lowercase
    const lowercase = section.toLowerCase();
    
    // Then replace spaces with hyphens (avoiding regex in template)
    const hyphenated = lowercase.split(' ').join('-');
    
    // Return with the prefix
    return `${prefix}-${hyphenated}`;
  }
  
  ngAfterViewInit() {
    // Syntax highlight all code blocks
    setTimeout(() => {
      hljs.highlightAll();
    }, 100);
  }

  async loadContractData() {
    try {
      // First try to get data from current_analysis
      const currentAnalysis = localStorage.getItem('current_analysis');
      console.log('Raw current_analysis:', currentAnalysis);
      
      if (currentAnalysis) {
        const analysisData = JSON.parse(currentAnalysis);
        this.rawData = analysisData; // Store raw data for debugging
        this.fileName = analysisData.fileName || 'Unknown Document';
        this.analysisType = analysisData.type || 'Contract Analysis';
        this.analysisDate = analysisData.analysisDate ? new Date(analysisData.analysisDate) : new Date();
        
        // Format the data to match our interface
        if (analysisData.result) {
          // If result is a string, put it in Contract Review
          if (typeof analysisData.result === 'string') {
            const html: string = marked.parse(analysisData.result, { async: false }) as string;
            this.contractData = {
              'Contract Review': this.sanitizer.bypassSecurityTrustHtml(html)
            };
          } 
          // If result is an object, map it to our interface
          else if (typeof analysisData.result === 'object') {
            this.contractData = await this.formatContractData(analysisData.result);
          }
        }
        
        console.log('Formatted contract data:', this.contractData);
      } 
      // Fallback to contract_review
      else {
        const contractReviewData = localStorage.getItem('contract_review');
        console.log('Raw contract_review data:', contractReviewData);
        
        if (contractReviewData) {
          const reviewData = JSON.parse(contractReviewData);
          this.rawData = reviewData; // Store raw data for debugging
          this.fileName = reviewData.fileName || 'Unknown Document';
          this.analysisType = 'contract_review';
          this.analysisDate = reviewData.analysisDate ? new Date(reviewData.analysisDate) : new Date();
          
          if (reviewData.result) {
            // Handle different data formats
            if (typeof reviewData.result === 'string') {
              const html: string = marked.parse(reviewData.result, { async: false }) as string;
              this.contractData = {
                'Contract Review': this.sanitizer.bypassSecurityTrustHtml(html)
              };
            } else if (typeof reviewData.result === 'object') {
              this.contractData = await this.formatContractData(reviewData.result);
            } else {
              // Fall back to raw data if we can't parse the result
              this.contractData = {
                'Raw Data': reviewData
              };
            }
          } else if (typeof reviewData === 'object') {
            // If no result property, try to use the root object
            this.contractData = await this.formatContractData(reviewData);
          }
        }
      }
      
      // If no data is found in either location
      if (!this.contractData) {
        console.warn('No contract data found in localStorage');
        // Add a debug section showing what's in localStorage
        const localStorageKeys = Object.keys(localStorage);
        this.contractData = {
          'Debug Info': this.sanitizer.bypassSecurityTrustHtml(
            `<p>No contract data found in localStorage.</p>
             <p>Available localStorage keys: ${localStorageKeys.join(', ')}</p>`
          )
        };
      }
    } catch (error: unknown) {
      console.error('Error loading contract data:', error);
      
      // Create a safe error message that works with any error type
      let errorMessage = 'An unknown error occurred';
      let errorStack = '';
      
      if (error instanceof Error) {
        errorMessage = error.message;
        errorStack = error.stack || '';
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (error && typeof error === 'object') {
        // Try to get a string representation
        errorMessage = String(error);
      }
      
      // Show error message
      this.contractData = {
        'Error': this.sanitizer.bypassSecurityTrustHtml(
          `<p>Error loading contract data: ${errorMessage}</p>
           <pre>${errorStack}</pre>`
        )
      };
    } finally {
      this.isLoading = false;
    }
  }

  // Format data to match our interface
  async formatContractData(data: any): Promise<ContractData> {
    console.log('Formatting contract data:', data);
    const formattedData: ContractData = {};
    
    // Map known fields to our interface
    if (data.summary) {
      const html: string = marked.parse(data.summary, { async: false }) as string;
      formattedData['Contract Review'] = this.sanitizer.bypassSecurityTrustHtml(html);
    }
    
    if (data.key_terms || data.key_provisions) {
      const content = await this.formatArrayOrString(data.key_terms || data.key_provisions);
      const html: string = marked.parse(content, { async: false }) as string;
      formattedData['Key Terms'] = this.sanitizer.bypassSecurityTrustHtml(html);
    }
    
    if (data.obligations) {
      const content = await this.formatArrayOrString(data.obligations);
      const html: string = marked.parse(content, { async: false }) as string;
      formattedData['Obligations'] = this.sanitizer.bypassSecurityTrustHtml(html);
    }
    
    if (data.parties) {
      const content = await this.formatArrayOrString(data.parties);
      const html: string = marked.parse(content, { async: false }) as string;
      formattedData['Parties'] = this.sanitizer.bypassSecurityTrustHtml(html);
    }
    
    // Include other fields that might be present
    for (const key in data) {
      if (!formattedData[key] && !['summary', 'key_terms', 'key_provisions', 'obligations', 'parties'].includes(key)) {
        const content = await this.formatArrayOrString(data[key]);
        try {
          const html: string = marked.parse(content, { async: false }) as string;
          formattedData[key] = this.sanitizer.bypassSecurityTrustHtml(html);
        } catch (err) {
          console.error(`Error parsing content for ${key}:`, err);
          // Use plain text as fallback
          formattedData[key] = this.sanitizer.bypassSecurityTrustHtml(`<pre>${content}</pre>`);
        }
      }
    }
    
    // If no sections were found, add raw data for debugging
    if (Object.keys(formattedData).length === 0) {
      formattedData['Raw Data'] = this.sanitizer.bypassSecurityTrustHtml(
        `<pre>${JSON.stringify(data, null, 2)}</pre>`
      );
    }
    
    // Make sure we have all our standard sections, even if empty
    if (!formattedData['Contract Review']) formattedData['Contract Review'] = '';
    if (!formattedData['Key Terms']) formattedData['Key Terms'] = '';
    if (!formattedData['Obligations']) formattedData['Obligations'] = '';
    if (!formattedData['Parties']) formattedData['Parties'] = '';
    
    return formattedData;
  }

  // Helper to format array data as a string with markdown
  async formatArrayOrString(data: any): Promise<string> {
    if (Array.isArray(data)) {
      return data.map((item, index) => `${index + 1}. ${item}`).join('\n\n');
    } else if (typeof data === 'object' && data !== null) {
      return JSON.stringify(data, null, 2);
    } else {
      return String(data || '');
    }
  }

  setCurrentSection(section: string) {
    this.currentSection = section;
  }

  // Get available sections from the data for dynamic tab generation
  getSections(): string[] {
    if (!this.contractData) return [];
    return Object.keys(this.contractData).filter(key => 
      this.contractData![key] && 
      (typeof this.contractData![key] === 'object' ||
      typeof this.contractData![key] === 'string' && this.contractData![key].toString().trim() !== '')
    );
  }

  // Return to contracts list
  backToContracts() {
    this.router.navigate(['/Contract']);
  }

  // Debug: Reload data
  reloadData() {
    this.isLoading = true;
    this.contractData = null;
    this.loadContractData();
  }

  // Method to print the analysis
  printAnalysis(): void {
    window.print();
  }

  // View mode methods
  setViewMode(mode: 'cards' | 'list' | 'compact'): void {
    this.viewMode = mode;
    // Save user preference in localStorage
    localStorage.setItem('contract_review_view_mode', mode);
  }

  // Method to scroll to a specific section
  scrollToSection(sectionId: string): void {
    const element = document.getElementById(sectionId);
    if (element) {
      // Smooth scroll to the element with offset for header
      const headerOffset = 80;
      const elementPosition = element.getBoundingClientRect().top;
      const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
      
      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
      });
    }
  }
}