// contract-review.component.ts
import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatExpansionModule } from '@angular/material/expansion';

interface ContractData {
  'Contract Review': string;
  'Key Terms': string;
  'Obligations': string;
  'Parties': string;
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
    MatExpansionModule
  ]
})
export class ContractReviewComponent {
  contractData: ContractData | null = null;
  isLoading = true;
  currentSection = 'all';

  ngOnInit() {
    try {
      const data = localStorage.getItem('contract_review');
      if (data) {
        this.contractData = JSON.parse(data);
        console.log('Contract Data:', this.contractData);
      }
    } catch (error) {
      console.error('Error loading contract data:', error);
    } finally {
      this.isLoading = false;
    }
  }

  setCurrentSection(section: string) {
    this.currentSection = section;
  }
}