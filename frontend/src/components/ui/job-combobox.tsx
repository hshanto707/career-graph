// Selection-only autocomplete for picking an actual Job record (id +
// label). Unlike `Combobox`, typed text is never committed as the value on
// its own -- only choosing a suggestion calls `onSelect`, because a target
// role must resolve to a real Job.id for gap analysis to work at all.
import * as React from "react";
import { Check, ChevronsUpDown, Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";

export interface JobOption {
  id: string;
  label: string;
}

export interface JobComboboxProps {
  query: string;
  onQueryChange: (query: string) => void;
  onSelect: (option: JobOption) => void;
  options: JobOption[];
  isLoading?: boolean;
  placeholder?: string;
  id?: string;
  "aria-label"?: string;
  selectedId?: string | null;
}

export const JobCombobox = React.forwardRef<HTMLInputElement, JobComboboxProps>(
  (
    { query, onQueryChange, onSelect, options, isLoading, placeholder, id, "aria-label": ariaLabel, selectedId },
    ref
  ) => {
    const [open, setOpen] = React.useState(false);

    return (
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <div className="relative">
            <input
              ref={ref}
              id={id}
              aria-label={ariaLabel}
              value={query}
              placeholder={placeholder}
              onChange={(e) => {
                onQueryChange(e.target.value);
                if (!open) setOpen(true);
              }}
              onFocus={() => setOpen(true)}
              autoComplete="off"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 pr-8 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            />
            <ChevronsUpDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 shrink-0 opacity-50 pointer-events-none" />
          </div>
        </PopoverTrigger>
        <PopoverContent
          className="w-[--radix-popover-trigger-width] p-0"
          align="start"
          onOpenAutoFocus={(e) => e.preventDefault()}
        >
          <Command shouldFilter={false}>
            <CommandList>
              {isLoading ? (
                <div className="flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Loading…
                </div>
              ) : options.length === 0 ? (
                <CommandEmpty>
                  {query.trim() ? "No matching jobs found." : "Type to search for a job."}
                </CommandEmpty>
              ) : (
                <CommandGroup>
                  {options.map((option) => (
                    <CommandItem
                      key={option.id}
                      value={option.id}
                      onSelect={() => {
                        onSelect(option);
                        setOpen(false);
                      }}
                    >
                      <Check
                        className={cn("mr-2 h-4 w-4", selectedId === option.id ? "opacity-100" : "opacity-0")}
                      />
                      {option.label}
                    </CommandItem>
                  ))}
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    );
  }
);
JobCombobox.displayName = "JobCombobox";
