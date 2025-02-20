import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

interface ExtractionResult {
  term: string;
  extracted_value: string;
  timestamp: string;
}

interface ExtractionData {
  'Information Extraction': {
    results: ExtractionResult[];
  }
}

@Component({
  selector: 'app-extraction',
  imports: [CommonModule],
  templateUrl: './extraction.component.html',
  styleUrl: './extraction.component.scss',
  standalone: true,
})
export class ExtractionComponent implements OnInit {
  extractionData: ExtractionResult[] = [];
  currentPage: number = 1;
  itemsPerPage: number = 10;

  ngOnInit(): void {
    this.loadExtractionData();
  }

  loadExtractionData(): void {
    try {
      const rawData = localStorage.getItem('extraction');
      if (!rawData) {
        console.warn('No extraction data found in localStorage');
        return;
      }

      const parsedData: ExtractionData = JSON.parse(rawData);
      this.extractionData = parsedData['Information Extraction']?.results || [];
    } catch (error) {
      console.error('Error loading extraction data:', error);
      this.extractionData = [];
    }
  }

  refreshData(): void {
    this.loadExtractionData();
  }

  get totalPages(): number {
    return Math.ceil(this.extractionData.length / this.itemsPerPage);
  }

  get paginatedData(): ExtractionResult[] {
    const startIndex = (this.currentPage - 1) * this.itemsPerPage;
    return this.extractionData.slice(startIndex, startIndex + this.itemsPerPage);
  }

  nextPage(): void {
    if (this.currentPage < this.totalPages) {
      this.currentPage++;
    }
  }

  previousPage(): void {
    if (this.currentPage > 1) {
      this.currentPage--;
    }
  }
}
