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
  loading: boolean = true;
  error: string | null = null;

  ngOnInit(): void {
    this.loadExtractionData();
  }

  loadExtractionData(): void {
    this.loading = true;
    this.error = null;
    
    try {
      // First try to get data from 'extraction' key (preferred format)
      let rawData = localStorage.getItem('extraction');
      
      // If no data found, try current_analysis as fallback
      if (!rawData) {
        console.log('No data in "extraction", checking "current_analysis"...');
        const currentAnalysis = localStorage.getItem('current_analysis');
        
        if (currentAnalysis) {
          const analysisData = JSON.parse(currentAnalysis);
          
          if (analysisData.type === 'information_extraction' && analysisData.result) {
            console.log('Found extraction data in current_analysis, converting format...');
            
            // Convert and format the extraction data
            let results: ExtractionResult[] = [];
            const result = analysisData.result;
            
            // Handle different possible formats
            if (Array.isArray(result)) {
              results = result.map(this.formatExtractionItem);
            } else if (typeof result === 'object' && result !== null) {
              // Check if it has Information Extraction structure
              if (result['Information Extraction'] && 
                  result['Information Extraction'].results) {
                results = result['Information Extraction'].results;
              } else {
                // Handle key-value object
                results = Object.entries(result).map(([term, value]) => ({
                  term,
                  extracted_value: typeof value === 'object' ? 
                    JSON.stringify(value) : String(value),
                  timestamp: new Date().toISOString()
                }));
              }
            } else {
              // Simple value
              results = [{
                term: 'Result',
                extracted_value: String(result),
                timestamp: new Date().toISOString()
              }];
            }
            
            // Create properly formatted data
            const extractionData = {
              'Information Extraction': {
                results: results
              }
            };
            
            // Save in the correct format for next time
            localStorage.setItem('extraction', JSON.stringify(extractionData));
            rawData = JSON.stringify(extractionData);
          }
        }
      }
      
      if (!rawData) {
        console.warn('No extraction data found in localStorage');
        this.error = 'No extraction data found. Please run an extraction analysis first.';
        this.extractionData = [];
        this.loading = false;
        return;
      }

      console.log('Parsing extraction data:', rawData);
      
      try {
        const parsedData: ExtractionData = JSON.parse(rawData);
        
        if (parsedData['Information Extraction']?.results) {
          // Process each item to ensure proper format
          this.extractionData = parsedData['Information Extraction'].results.map(
            item => this.formatExtractionItem(item)
          );
          console.log('Loaded extraction data successfully:', this.extractionData);
        } else {
          console.error('Invalid extraction data format:', parsedData);
          this.error = 'Invalid data format. Please try running the extraction again.';
          this.extractionData = [];
        }
      } catch (parseError) {
        console.error('Error parsing JSON data:', parseError);
        this.error = 'Invalid data format. Please try running the extraction again.';
        this.extractionData = [];
      }
    } catch (error) {
      console.error('Error loading extraction data:', error);
      this.error = 'Error loading extraction data. Please try again.';
      this.extractionData = [];
    } finally {
      this.loading = false;
    }
  }

  // Helper method to ensure consistent item format and handle nested objects
  private formatExtractionItem(item: any): ExtractionResult {
    if (typeof item !== 'object' || item === null) {
      return {
        term: 'Unknown',
        extracted_value: String(item),
        timestamp: new Date().toISOString()
      };
    }
    
    return {
      term: item.term || 'Unknown',
      extracted_value: typeof item.extracted_value === 'object' ? 
        JSON.stringify(item.extracted_value) : 
        String(item.extracted_value || ''),
      timestamp: item.timestamp || new Date().toISOString()
    };
  }

  refreshData(): void {
    this.loadExtractionData();
  }
}