import { Component } from '@angular/core';
import { AuthService } from '../../../auth/auth.service';

@Component({
    selector: 'app-header',
    templateUrl: './header.component.html',
    styleUrls: ['./header.component.scss'],
    standalone: false
})
export class HeaderComponent {
  title = 'CLM Pro';

  constructor(private authService: AuthService) {}

  logout() {
    this.authService.logout();
  }
}