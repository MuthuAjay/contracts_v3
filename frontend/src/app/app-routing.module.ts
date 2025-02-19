import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { UserManagementComponent } from './components/user-management/user-management.component';
import { KeywordsManagementComponent } from './components/keywords-management/keywords-management.component';
import { ChatbotComponent } from './components/chatbot/chatbot.component';
import { SettingsComponent } from './components/settings/settings.component';
import { HelpComponent } from './components/help/help.component';
import { UserProfileComponent } from './components/user-profile/user-profile.component';
import { LoginComponent } from './auth/login/login.component';
import { SignupComponent } from './auth/signup/signup.component';
import { AuthGuard } from './auth/auth.guard';
import { ReviewComponent } from './components/review/review.component';
import { ExtractionComponent } from './components/extraction/extraction.component';

const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'signup', component: SignupComponent },
  { path: '', redirectTo: '/login', pathMatch: 'full',},
  { path: 'dashboard', component: DashboardComponent,},
  { path: 'Contract', component: UserManagementComponent,},
  { path: 'Template', component: KeywordsManagementComponent,},
  { path: 'Analytics', component: ChatbotComponent,},
  { path: 'Compliance', component: SettingsComponent,},
  { path: 'Collaboration', component: HelpComponent,},
  { path: 'profile', component: UserProfileComponent,},
  { path: 'Integration', component: ReviewComponent,},
  { path: 'extraction', component: ExtractionComponent,}
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})
export class AppRoutingModule { }