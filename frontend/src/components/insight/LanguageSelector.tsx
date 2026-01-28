import { useState, useEffect, useRef } from 'react';
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

  // ✅ separate states
  const [selectOpen, setSelectOpen] = useState(false);
  const [customOpen, setCustomOpen] = useState(false);

  const inputRef = useRef<HTMLInputElement | null>(null);

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

  // When custom popup opens, focus the input
  useEffect(() => {
    if (customOpen) {
      // next tick to ensure it's mounted
      setTimeout(() => inputRef.current?.focus(), 0);
    }
  }, [customOpen]);

  const handleOptionChange = (value: LanguageOption) => {
    setSelectedOption(value);

    if (value === 'en') {
      localStorage.setItem(STORAGE_KEY, 'en');
      setSelectOpen(false);
      setCustomOpen(false);
      return;
    }

    if (value === 'de') {
      localStorage.setItem(STORAGE_KEY, 'de');
      setSelectOpen(false);
      setCustomOpen(false);
      return;
    }

    setSelectOpen(false);
    setCustomOpen(true);
  };

  const handleCustomLanguageChange = (value: string) => {
    setCustomLanguage(value);
    const trimmed = value.trim();
    if (trimmed) {
      localStorage.setItem(STORAGE_KEY, trimmed);
    }
  };

  const commitAndCloseCustom = () => {
    const trimmed = customLanguage.trim();
    if (trimmed) {
      localStorage.setItem(STORAGE_KEY, trimmed);
    }
    setCustomOpen(false);
  };

  return (
    <div className="flex items-center gap-2">
      <div className="hidden sm:flex items-center gap-1.5 text-xs text-muted-foreground">
        <Globe className="h-3.5 w-3.5" />
        <span className="hidden md:inline">Report & Chat</span>
      </div>
      <div className="flex flex-col gap-1 relative">
        <Select
          value={selectedOption}
          onValueChange={handleOptionChange}
          open={selectOpen}
          onOpenChange={setSelectOpen}
        >
          <SelectTrigger className="h-8 w-[100px] sm:w-[120px] text-xs bg-muted/50 border-border">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-background border-border">
            <SelectItem value="en" className="text-xs">English</SelectItem>
            <SelectItem value="de" className="text-xs">German</SelectItem>
            <SelectItem value="other" className="text-xs">Other…</SelectItem>
          </SelectContent>
        </Select>
        {selectedOption === 'other' && customOpen && (
          <div className="absolute top-full right-0 mt-1 z-50 flex flex-col gap-1 p-2 rounded-lg bg-background border border-border shadow-lg min-w-[200px]">
            <Input
              ref={inputRef}
              value={customLanguage}
              onChange={(e) => handleCustomLanguageChange(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  commitAndCloseCustom();
                }
                if (e.key === 'Escape') {
                  e.preventDefault();
                  setCustomOpen(false);
                }
              }}
              placeholder="e.g., Spanish, Hindi"
              className="h-8 text-xs bg-muted/50 border-border"
            />
            <span className="text-[10px] text-muted-foreground">
              Press Enter to apply.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}