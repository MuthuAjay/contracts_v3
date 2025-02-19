import { Component } from '@angular/core';

@Component({
    selector: 'app-keywords-management',
    templateUrl: './keywords-management.component.html',
    styleUrls: ['./keywords-management.component.scss'],
    standalone: false
})
export class KeywordsManagementComponent {
  keywords = [
    { id: 1, keyword: 'Angular', category: 'Framework' },
    { id: 2, keyword: 'TypeScript', category: 'Language' }
  ];

  displayedColumns: string[] = ['id', 'keyword', 'category', 'actions'];
}