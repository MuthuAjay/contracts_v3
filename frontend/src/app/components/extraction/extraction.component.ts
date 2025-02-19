import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

@Component({
  selector: 'app-extraction',
  imports: [CommonModule],
  templateUrl: './extraction.component.html',
  styleUrl: './extraction.component.scss',
  standalone: true,
})
export class ExtractionComponent {
extractionData:any
ngOnInit(){
  const data:any = localStorage.getItem('extraction')
  this.extractionData = JSON.parse(data)['Information Extraction']['results']
  console.log(this.extractionData)
}
}
