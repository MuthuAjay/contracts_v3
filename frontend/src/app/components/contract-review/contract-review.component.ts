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

// Define the highlight function type
interface MarkedHighlightOptions {
  highlight: (code: string, lang: string) => string;
  langPrefix?: string;
  baseUrl?: string;
  breaks?: boolean;
  gfm?: boolean;
  headerIds?: boolean;
  mangle?: boolean;
  pedantic?: boolean;
  sanitize?: boolean;
  sanitizer?: {
      (input: string): string;
  };
  silent?: boolean;
  smartLists?: boolean;
  smartypants?: boolean;
  xhtml?: boolean;
}

// Configure marked to use highlight.js for code syntax highlighting
marked.setOptions(<MarkedHighlightOptions>{
  highlight: function (code: string, lang: string) {
    return hljs.highlight(code, { language: lang }).value;
  },
  breaks: true, // Enable line breaks with single line breaks
  gfm: true,    // Enable GitHub Flavored Markdown
});

interface ContractData {
  'Contract Review'?: string;
  'Key Terms'?: string;
  'Obligations'?: string;
  'Parties'?: string;
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
    LineToBrPipe
  ]
})
export class ContractReviewComponent implements OnInit, AfterViewInit {
  contractData: ContractData | null = null;
  isLoading = true;
  currentSection = 'all';
  fileName: string = '';
  analysisType: string = '';
  analysisDate: Date | null = null;

  constructor(private router: Router) {}

  ngOnInit() {
    this.loadContractData();
  }

  ngAfterViewInit() {
    // Syntax highlight all code blocks
    hljs.highlightAll();
  }

  async loadContractData() {
    try {
      // First try to get data from current_analysis
      const currentAnalysis = localStorage.getItem('current_analysis');
      
      if (currentAnalysis) {
        const analysisData = JSON.parse(currentAnalysis);
        this.fileName = analysisData.fileName;
        this.analysisType = analysisData.type;
        this.analysisDate = new Date(analysisData.analysisDate);
        
        // Format the data to match our interface
        if (analysisData.result) {
          // If result is a string, put it in Contract Review
          if (typeof analysisData.result === 'string') {
            this.contractData = {
              'Contract Review': analysisData.result
            };
          } 
          // If result is an object, map it to our interface
          else if (typeof analysisData.result === 'object') {
            this.contractData = await this.formatContractData(analysisData.result);
          }
        }
        
        console.log('Contract Data (from current_analysis):', this.contractData);
      } 
      // Fallback to contract_review
      else {
        const contractReviewData = localStorage.getItem('contract_review');
        
        if (contractReviewData) {
          const reviewData = JSON.parse(contractReviewData);
          this.fileName = reviewData.fileName || '';
          this.analysisType = 'contract_review';
          this.analysisDate = reviewData.analysisDate ? new Date(reviewData.analysisDate) : null;
          
          if (reviewData.result) {
            // Handle different data formats
            if (typeof reviewData.result === 'string') {
              this.contractData = {
                'Contract Review': reviewData.result
              };
            } else if (typeof reviewData.result === 'object') {
              this.contractData = await this.formatContractData(reviewData.result);
            } else {
              this.contractData = reviewData; // Directly use the data if it's not nested under result
            }
          } else {
            this.contractData = reviewData; // Directly use the data if result is not present
          }
          
          console.log('Contract Data (from contract_review):', this.contractData);
        }
      }
      
      // If no data is found in either location
      if (!this.contractData) {
        console.warn('No contract data found in localStorage');
      }
    } catch (error) {
      console.error('Error loading contract data:', error);
    } finally {
      this.isLoading = false;
    }
  }

  // Format data to match our interface
  async formatContractData(data: any): Promise<ContractData> {
    const formattedData: ContractData = {};
    
    // Map known fields to our interface
    if (data.summary) {
      formattedData['Contract Review'] = data.summary;
    }
    
    if (data.key_terms || data.key_provisions) {
      formattedData['Key Terms'] = await this.formatArrayOrString(data.key_terms || data.key_provisions);
    }
    
    if (data.obligations) {
      formattedData['Obligations'] = await this.formatArrayOrString(data.obligations);
    }
    
    if (data.parties) {
      formattedData['Parties'] = await this.formatArrayOrString(data.parties);
    }
    
    // Include other fields that might be present
    for (const key in data) {
      if (!formattedData[key] && !['summary', 'key_terms', 'key_provisions', 'obligations', 'parties'].includes(key)) {
        formattedData[key] = await this.formatArrayOrString(data[key]);
      }
    }
    
    // Make sure we have all our standard sections, even if empty
    if (!formattedData['Contract Review']) formattedData['Contract Review'] = '';
    if (!formattedData['Key Terms']) formattedData['Key Terms'] = '';
    if (!formattedData['Obligations']) formattedData['Obligations'] = '';
    if (!formattedData['Parties']) formattedData['Parties'] = '';
    
    return formattedData;
  }

  // Helper to format array data as a string
  async formatArrayOrString(data: any): Promise<string> {
    if (Array.isArray(data)) {
      return data.map((item, index) => `${index + 1}. ${item}`).join('\n\n');
    } else if (typeof data === 'object' && data !== null) {
      return JSON.stringify(data, null, 2);
    } else {
      // Convert Markdown to HTML
      return marked.parseInline(String(data || ''));
    }
  }

  setCurrentSection(section: string) {
    this.currentSection = section;
  }

  // Get available sections from the data for dynamic tab generation
  getSections(): string[] {
    if (!this.contractData) return [];
    return Object.keys(this.contractData).filter(key => 
      this.contractData![key] && this.contractData![key].trim() !== ''
    );
  }

  // Return to contracts list
  backToContracts() {
    this.router.navigate(['/Contract']);
  }
}