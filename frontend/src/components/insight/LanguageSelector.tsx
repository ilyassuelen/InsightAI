import { useState, useEffect } from 'react';
import { Globe } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';

const STORAGE_KEY = 'reportChatLanguage';

type LanguageOption = 'en' | 'de' | 'other';

export function LanguageSelector() {
  const [selectedOption, setSelectedOption] = useState<LanguageOption>('de');
  const [customLanguage, setCustomLanguage] = useState('');

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'en') {
      setSelectedOption('en');
    } else if (stored === 'de' || !stored) {
      setSelectedOption('de');
    } else {
      setSelectedOption('other');
      setCustomLanguage(stored);
    }
  }, []);

  const handleOptionChange = (value: LanguageOption) => {
    setSelectedOption(value);
    if (value === 'en') {
      localStorage.setItem(STORAGE_KEY, 'en');
    } else if (value === 'de') {
      localStorage.setItem(STORAGE_KEY, 'de');
    }
    // For 'other', we save when the input changes
  };

  const handleCustomLanguageChange = (value: string) => {
    setCustomLanguage(value);
    const trimmed = value.trim();
    if (trimmed) {
      localStorage.setItem(STORAGE_KEY, trimmed);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <div className="hidden sm:flex items-center gap-1.5 text-xs text-muted-foreground">
        <Globe className="h-3.5 w-3.5" />
        <span className="hidden md:inline">Report & Chat</span>
      </div>
      
      <div className="flex flex-col gap-1">
        <Select value={selectedOption} onValueChange={handleOptionChange}>
          <SelectTrigger className="h-8 w-[100px] sm:w-[120px] text-xs bg-muted/50 border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-background border-border">
            <SelectItem value="en" className="text-xs">English</SelectItem>
            <SelectItem value="de" className="text-xs">German</SelectItem>
            <SelectItem value="other" className="text-xs">Other…</SelectItem>
          </SelectContent>
        </Select>
        
        {selectedOption === 'other' && (
          <div className="absolute top-full right-0 mt-1 z-50 flex flex-col gap-1 p-2 rounded-lg bg-background border border-border shadow-lg min-w-[200px]">
            <Input
              value={customLanguage}
              onChange={(e) => handleCustomLanguageChange(e.target.value)}
              placeholder="e.g., Spanish, Hindi"
              className="h-8 text-xs bg-muted/50 border-border"
            />
            <span className="text-[10px] text-muted-foreground">
              AI outputs will be generated in this language.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
