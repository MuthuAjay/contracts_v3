import { ComponentFixture, TestBed } from '@angular/core/testing';

import { LegalResearchComponent } from './legal-research.component';

describe('LegalResearchComponent', () => {
  let component: LegalResearchComponent;
  let fixture: ComponentFixture<LegalResearchComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LegalResearchComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(LegalResearchComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
