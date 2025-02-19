import { Component } from '@angular/core';
interface TabItem {
  title: string;
  description: string;
  image: string;
}
@Component({
  selector: 'app-review',
  imports: [],
  templateUrl: './review.component.html',
  styleUrl: './review.component.scss'
})
export class ReviewComponent {
  tabs: TabItem[] = [
    {
      title: 'Tab 1',
      description: 'Detailed description for Tab 1 goes here. You can add any text or information that you want to display when this tab is selected.',
      image: 'https://via.placeholder.com/400x300'
    },
    {
      title: 'Tab 2',
      description: 'Detailed description for Tab 2 goes here. This is where you can provide more information about the second tab.',
      image: 'https://via.placeholder.com/400x300/ff0000'
    },
    {
      title: 'Tab 3', 
      description: 'Detailed description for Tab 3 goes here. Feel free to customize the content as needed.',
      image: 'https://via.placeholder.com/400x300/00ff00'
    }
  ];

  activeTabIndex = 0;
}
