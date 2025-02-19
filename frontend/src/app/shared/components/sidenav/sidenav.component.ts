import { Component, ElementRef, ViewChild } from '@angular/core';

@Component({
    selector: 'app-sidenav',
    templateUrl: './sidenav.component.html',
    styleUrls: ['./sidenav.component.scss'],
    standalone: false
})
export class SidenavComponent {
  @ViewChild('sidebar') sidebar: ElementRef | undefined;

  menuItems = [
    { path: '/dashboard', icon: 'fa-solid fa-chart-line', label: 'Dashboard' },
    { path: '/Contract', icon: 'fa-regular fa-user', label: 'Contracts' },
    { path: '/Template', icon: 'fa-regular fa-keyboard', label: 'Templates' },
    { path: '/Analytics', icon: 'fa-brands fa-react', label: 'Analytics' },
    { path: '/Compliance', icon: 'fa-regular fa-message', label: 'Compliance' },
    { path: '/Collaboration', icon: 'fa-solid fa-info', label: 'Collaborate' },
    { path: '/Integration', icon: 'fa-solid fa-info', label: 'Integrate' }
  ];

  // Function to toggle sidebar open class
  toggleSidebar(): void {
    if (this.sidebar) {
      this.sidebar.nativeElement.classList.toggle("open");
    }
  }

  // Function to change the menu button icon
  menuBtnChange(target: EventTarget | null): void {
    if (target instanceof HTMLElement && this.sidebar) {
      if (this.sidebar.nativeElement.classList.contains("open")) {
        target.classList.replace("fa-bars", "fa-solid fa-xmark");
      } else {
        target.classList.replace("fa-solid fa-bars", "fa-bars");
      }
    }
  }
}
