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
import { MatTabsModule } from '@angular/material/tabs';
import { Router } from '@angular/router';
import { DomSanitizer } from '@angular/platform-browser';
import { marked } from 'marked';

// Configure marked options for better list handling
marked.setOptions({
  breaks: true,
  gfm: true
});

@Component({
  selector: 'app-risk-assessment',
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
    MatTabsModule,
    LineToBrPipe
  ],
  templateUrl: './risk-assessment.component.html',
  styleUrl: './risk-assessment.component.scss'
})
export class RiskAssessmentComponent implements OnInit {
  contractData: any = null;
  isLoading = true;
  currentSection = 'all';
  fileName: string = '';
  analysisType: string = '';
  analysisDate: Date | null = null;
  rawData: any = null; // Store raw data for debugging
  
  // Define standard risk categories and a map for icons
  riskCategories = ['all', 'legal', 'financial', 'operational', 'compliance'];
  categoryIcons: { [key: string]: string } = {
    'all': 'assessment',
    'legal': 'gavel',
    'financial': 'attach_money',
    'operational': 'build',
    'compliance': 'verified_user'
  };

  constructor(private router: Router, private sanitizer: DomSanitizer) {}
  
  ngOnInit() {
    this.loadContractData();
  }

  // Return to contracts list
  backToContracts() {
    this.router.navigate(['/Contract']);
  }

  // Change the currently viewed section
  changeSection(section: string) {
    this.currentSection = section;
  }

  getSections(): string[] {
    if (!this.contractData) return [];
    return Object.keys(this.contractData).filter(key => 
      this.contractData![key] && 
      typeof this.contractData![key] === 'object' && 
      key !== 'Raw Data'
    );
  }

  // Get all available risk categories
  getCategories(): string[] {
    const standardCategories = ['all', 'legal', 'financial', 'operational', 'compliance'];
    
    if (!this.contractData) return standardCategories;
    
    // Add any additional categories from the data
    const additionalCategories = Object.keys(this.contractData)
      .filter(key => 
        !standardCategories.includes(key) && 
        this.contractData![key] && 
        key !== 'Raw Data'
      );
    
    return [...standardCategories, ...additionalCategories];
  }

  // Get icon for category
  getCategoryIcon(category: string): string {
    return this.categoryIcons[category] || 'assessment';
  }

  getRiskLevel(section: string): string {
    if (!section || !this.contractData[section]) return 'unknown';
    
    const content = this.contractData[section].toString().toLowerCase();
    
    if (content.includes('high risk') || content.includes('critical risk') || 
        content.includes('severe risk')) {
      return 'high';
    } else if (content.includes('medium risk') || content.includes('moderate risk')) {
      return 'medium';
    } else if (content.includes('low risk') || content.includes('minimal risk')) {
      return 'low';
    }
    
    return 'unknown';
  }

  async loadContractData() {
    try {
      // Get data from localStorage
      const currentAnalysis = localStorage.getItem('risk_assessment');
      console.log("Risk assessment data:", currentAnalysis);
      
      if (currentAnalysis) {
        const analysisData = JSON.parse(currentAnalysis);
        this.rawData = analysisData; // Store for debugging
        this.fileName = analysisData.fileName || 'Unknown File';
        this.analysisType = analysisData.type || 'Risk Assessment';
        this.analysisDate = analysisData.analysisDate ? new Date(analysisData.analysisDate) : new Date();
        
        // Format the data
        if (analysisData.result) {
          // Process each risk category
          const formattedData: any = {};
          
          // Handle different response structures
          if (typeof analysisData.result === 'object') {
            Object.keys(analysisData.result).forEach(key => {
              const content = analysisData.result[key];
              if (typeof content === 'string' && content.trim() !== '') {
                try {
                  const html = marked.parse(content, { async: false }) as string;
                  formattedData[key] = this.sanitizer.bypassSecurityTrustHtml(html);
                } catch (err) {
                  console.error(`Error parsing markdown for ${key}:`, err);
                  formattedData[key] = content; // Use raw if parsing fails
                }
              } else if (typeof content === 'object') {
                // Handle nested objects (common in risk assessment)
                Object.keys(content).forEach(subKey => {
                  const subContent = content[subKey];
                  if (typeof subContent === 'string' && subContent.trim() !== '') {
                    try {
                      const html = marked.parse(subContent, { async: false }) as string;
                      formattedData[subKey] = this.sanitizer.bypassSecurityTrustHtml(html);
                    } catch (err) {
                      console.error(`Error parsing markdown for ${key}.${subKey}:`, err);
                      formattedData[subKey] = subContent; // Use raw if parsing fails
                    }
                  }
                });
              }
            });
            
            this.contractData = formattedData;
            
            // Add any missing categories with empty content
            this.riskCategories.forEach(category => {
              if (category !== 'all' && !this.contractData[category]) {
                this.contractData[category] = this.sanitizer.bypassSecurityTrustHtml('<p>No data available for this risk category.</p>');
              }
            });
          }
        }
        
        console.log('Formatted Risk Assessment Data:', this.contractData);
      }
    } catch (error) {
      console.error('Error loading risk assessment data:', error);
      // Show raw data if parsing fails
      const currentAnalysis = localStorage.getItem('risk_assessment');
      if (currentAnalysis) {
        try {
          this.contractData = {
            'Raw Data': JSON.parse(currentAnalysis).result
          };
        } catch (e) {
          console.error('Failed to display raw data:', e);
        }
      }
    } finally {
      this.isLoading = false;
    }
  }

  // Check if a section should be shown based on current filter
  shouldShowSection(section: string): boolean {
    if (this.currentSection === 'all') return true;
    return section === this.currentSection;
  }
}
