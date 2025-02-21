import { Component, OnInit, ViewChild, ElementRef, AfterViewChecked, OnDestroy } from '@angular/core';
import { ServicesService } from '../../services.service';
import { Subject, takeUntil } from 'rxjs';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

interface ChatMessage {
  id: string;
  content: string;
  isBot: boolean;
  timestamp: Date;
  status: 'sending' | 'sent' | 'error';
}

interface ExtractionData {
  type: string;
  custom_query: string;
  [key: string]: any;
}

interface ContractData {
  fileName: string;
  extractedData: any;
  contractId: string;
  [key: string]: any;
}

@Component({
  selector: 'app-chatbot',
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class ChatbotComponent implements OnInit, AfterViewChecked, OnDestroy {
  @ViewChild('messageContainer') private messageContainer!: ElementRef;
  @ViewChild('inputArea') private inputArea!: ElementRef;

  public messages: ChatMessage[] = [];
  public newMessage = '';
  public isLoading = false;
  public error: string | null = null;
  public loadershow = true;
  public currentContract: ContractData | null = null;
  
  private destroy$ = new Subject<void>();
  private readonly MAX_RETRIES = 3;
  private retryCount = 0;
  private resultSaved = false;

  constructor(
    private apiService: ServicesService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // First, check if we have a selected contract for custom analysis
    this.loadSelectedContract();
    
    // If no contract is selected, we might want to redirect back
    if (!this.currentContract) {
      console.warn('No contract selected for analysis');
      // Uncomment to redirect if no contract selected:
      // this.router.navigate(['/']);
      // return;
    }
    
    this.initializeChat();
    this.loadStoredMessages();
  }

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.saveMessages();
    
    // If we're navigating away without saving a result, clean up
    if (!this.resultSaved) {
      localStorage.removeItem('custom_analysis_contract');
    }
  }

  private loadSelectedContract(): void {
    try {
      const contractData = localStorage.getItem('custom_analysis_contract');
      if (contractData) {
        this.currentContract = JSON.parse(contractData);
        console.log('Loaded contract for analysis:', this.currentContract?.fileName);
      }
    } catch (error) {
      console.error('Error loading contract data:', error);
      this.currentContract = null;
    }
  }

  private initializeChat(): void {
    let welcomeMessage = 'Hello! How can I help you today?';
    
    // If we have a contract, customize the welcome message
    if (this.currentContract) {
      welcomeMessage = `Hello! I'm analyzing the document "${this.currentContract.fileName}". What would you like to know about it?`;
    }
    
    const botMessage: ChatMessage = {
      id: this.generateMessageId(),
      content: welcomeMessage,
      isBot: true,
      timestamp: new Date(),
      status: 'sent'
    };
    
    this.messages = [botMessage];
  }

  private loadStoredMessages(): void {
    try {
      // Only load stored messages if we're continuing with the same contract
      const currentContractId = this.currentContract?.contractId || '';
      const storedContractId = localStorage.getItem('chat_contract_id');
      
      if (storedContractId === currentContractId && currentContractId) {
        const storedMessages = localStorage.getItem('chatMessages');
        if (storedMessages) {
          const parsedMessages = JSON.parse(storedMessages);
          this.messages = parsedMessages.map((msg: any) => ({
            ...msg,
            timestamp: new Date(msg.timestamp)
          }));
        }
      } else if (currentContractId) {
        // If we're analyzing a different contract, store the new contract ID
        localStorage.setItem('chat_contract_id', currentContractId);
      }
    } catch (error) {
      console.error('Error loading stored messages:', error);
    }
  }

  private saveMessages(): void {
    try {
      localStorage.setItem('chatMessages', JSON.stringify(this.messages));
      
      // Also save the current contract ID to associate messages with this contract
      if (this.currentContract?.contractId) {
        localStorage.setItem('chat_contract_id', this.currentContract.contractId);
      }
    } catch (error) {
      console.error('Error saving messages:', error);
    }
  }

  public async sendMessage(): Promise<void> {
    if (!this.newMessage.trim() || this.isLoading) return;

    const userMessage: ChatMessage = {
      id: this.generateMessageId(),
      content: this.newMessage.trim(),
      isBot: false,
      timestamp: new Date(),
      status: 'sending'
    };

    this.messages.push(userMessage);
    this.isLoading = true;
    this.error = null;
    const messageContent = this.newMessage;
    this.newMessage = '';
    this.scrollToBottom();

    try {
      const extractedData = this.getExtractionData();
      const response = await this.sendMessageToApi(messageContent, extractedData);
      this.handleApiResponse(response);
      userMessage.status = 'sent';
    } catch (error) {
      this.handleError(error);
      userMessage.status = 'error';
    } finally {
      this.isLoading = false;
      this.saveMessages();
    }
  }

  private async sendMessageToApi(message: string, extractedData: ExtractionData) {
    return new Promise((resolve, reject) => {
      this.apiService.analyze({
        ...extractedData,
        type: 'custom_analysis',
        custom_query: message
      })
      .pipe(
        takeUntil(this.destroy$)
      )
      .subscribe({
        next: (response) => resolve(response),
        error: (error) => {
          if (this.retryCount < this.MAX_RETRIES) {
            this.retryCount++;
            setTimeout(() => {
              this.sendMessageToApi(message, extractedData)
                .then(resolve)
                .catch(reject);
            }, 1000 * this.retryCount);
          } else {
            this.retryCount = 0;
            reject(error);
          }
        }
      });
    });
  }

  private handleApiResponse(response: any): void {
    const botMessage: ChatMessage = {
      id: this.generateMessageId(),
      content: response['Custom Analysis'] || 'I apologize, but I couldn\'t process that properly.',
      isBot: true,
      timestamp: new Date(),
      status: 'sent'
    };
    
    this.messages.push(botMessage);
    this.scrollToBottom();
    
    // Save the analysis result when we get a valid response
    this.saveAnalysisResult(response);
  }
  
  private saveAnalysisResult(result: any): void {
    if (!this.currentContract) return;
    
    try {
      // Create the result object
      const resultData = {
        fileName: this.currentContract.fileName,
        result: result,
        type: 'custom_analysis',
        analysisDate: new Date()
      };
      
      // Save to localStorage for the main component to process
      localStorage.setItem('custom_analysis_result', JSON.stringify(resultData));
      localStorage.setItem('current_analysis', JSON.stringify(resultData));
      
      // Mark that we've saved the result
      this.resultSaved = true;
    } catch (error) {
      console.error('Error saving custom analysis result:', error);
    }
  }

  private handleError(error: any): void {
    console.error('Error in chat:', error);
    this.error = 'Sorry, there was an error processing your message. Please try again.';
    
    const errorMessage: ChatMessage = {
      id: this.generateMessageId(),
      content: this.error,
      isBot: true,
      timestamp: new Date(),
      status: 'error'
    };
    
    this.messages.push(errorMessage);
  }

  public onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.loadershow = false;
      this.sendMessage();
    }
  }

  private getExtractionData(): ExtractionData {
    // Use the current contract's extracted data if available
    if (this.currentContract && this.currentContract.extractedData) {
      console.log('Using extracted data from selected contract:', this.currentContract.fileName);
      return {
        ...this.currentContract.extractedData,
        type: 'custom_analysis',
        custom_query: ''
      };
    }
    
    // Fallback to localStorage as before
    try {
      console.log('No contract selected, falling back to localStorage extractionInfo');
      const extractedData = localStorage.getItem('extractionInfo');
      if (!extractedData) {
        return {
          type: 'custom_analysis',
          custom_query: ''
        };
      }
      return JSON.parse(extractedData);
    } catch (error) {
      console.error('Error parsing extraction data:', error);
      return {
        type: 'custom_analysis',
        custom_query: ''
      };
    }
  }

  private scrollToBottom(): void {
    try {
      this.messageContainer.nativeElement.scrollTop = 
        this.messageContainer.nativeElement.scrollHeight;
    } catch (err) {}
  }

  private generateMessageId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  public onInput(): void {
    const textarea = this.inputArea.nativeElement;
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  }

  public clearChat(): void {
    this.messages = [];
    this.initializeChat();
    localStorage.removeItem('chatMessages');
  }
  
  public returnToContracts(): void {
    this.router.navigate(['/Contract']);
  }
}