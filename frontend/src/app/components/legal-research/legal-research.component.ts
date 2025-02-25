import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { LineToBrPipe } from '../contract-review/line-to-br.pipe';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatIconModule } from '@angular/material/icon';
import { Router } from '@angular/router';
import { marked } from 'marked';

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
      LineToBrPipe
    ]
})
export class LegalResearchComponent {
  contractData: any = null;
  isLoading = true;
  currentSection = 'all';
  fileName: string = '';
  analysisType: string = '';
  analysisDate: Date | null = null;


   constructor(private router: Router) {}
  
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
      this.contractData![key] && this.contractData![key].trim() !== ''
    );
  }

  async loadContractData() {
    try {
      // First try to get data from current_analysis
      const currentAnalysis = localStorage.getItem('legal_research');

      console.log("info", currentAnalysis)
      
      if (currentAnalysis) {
        const analysisData = JSON.parse(currentAnalysis);
        this.fileName = analysisData.fileName;
        this.analysisType = analysisData.type;
        this.analysisDate = new Date(analysisData.analysisDate);
        
        // Format the data to match our interface
        if (analysisData.result) {
          // If result is a string, put it in Contract Review
          if (typeof analysisData.result['Legal Research'] === 'string') {
            this.contractData = {
              'Contract Review': analysisData.result['Legal Research']
            };
          } 
          // If result is an object, map it to our interface
          else if (typeof analysisData.result['Legal Research'] === 'object') {
            this.contractData = analysisData.result['Legal Research'];
          }
        }
        
        console.log('Contract Data (from current_analysis):', this.contractData);
      } 
      
      
     
    } catch (error) {
      console.error('Error loading contract data:', error);
    } finally {
      this.isLoading = false;
    }
  }
  



  
  

}
