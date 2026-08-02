import * as React from "react";
import { X, Plus, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Command, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";

const DEFAULT_SKILLS = [
  "JavaScript",
  "TypeScript",
  "Python",
  "React",
  "Node.js",
  "Java",
  "C++",
  "SQL",
  "PostgreSQL",
  "MongoDB",
  "AWS",
  "Docker",
  "Kubernetes",
  "Git",
  "HTML",
  "CSS",
  "Tailwind CSS",
  "Next.js",
  "GraphQL",
  "Machine Learning",
  "PyTorch",
  "TensorFlow",
  "Go",
  "Rust",
  "C#",
  ".NET",
  "Ruby",
  "Ruby on Rails",
  "PHP",
  "Laravel",
  "Swift",
  "Kotlin",
  "React Native",
  "Flutter",
  "Spring Boot",
];

export function SkillMultiSelect({
  selected,
  onChange,
}: {
  selected: string[];
  onChange: (selected: string[]) => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [inputValue, setInputValue] = React.useState("");

  const handleUnselect = (skill: string) => {
    onChange(selected.filter((s) => s !== skill));
  };

  const handleSelect = (skill: string) => {
    if (!selected.includes(skill)) {
      onChange([...selected, skill]);
    }
    setInputValue("");
  };

  // Predefined minus already selected
  const availableOptions = DEFAULT_SKILLS.filter((s) => !selected.includes(s));
  // If inputValue doesn't match any default strictly, we can show an "Add Custom" option
  const showCustomOption =
    inputValue.trim().length > 0 &&
    !DEFAULT_SKILLS.some((s) => s.toLowerCase() === inputValue.trim().toLowerCase()) &&
    !selected.some((s) => s.toLowerCase() === inputValue.trim().toLowerCase());

  return (
    <div className="flex flex-col gap-3">
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2 rounded-lg border border-border p-3 bg-card min-h-[50px] shadow-sm">
          {selected.map((skill) => (
            <Badge
              key={skill}
              variant="secondary"
              className="px-2.5 py-1 text-sm flex items-center gap-1.5 shadow-sm border border-border/50"
            >
              {skill}
              <button
                type="button"
                className="rounded-full outline-none hover:bg-muted focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-colors"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleUnselect(skill);
                }}
                onMouseDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                onClick={() => handleUnselect(skill)}
              >
                <X className="h-3 w-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-full justify-between text-muted-foreground shadow-sm h-11 bg-card"
          >
            Select or type skills...
            <Search className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
          <Command shouldFilter={false}>
            <div className="flex items-center border-b px-3">
              <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
              <input
                className="flex h-10 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
                placeholder="Search or add a custom skill..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && showCustomOption) {
                    handleSelect(inputValue.trim());
                    e.preventDefault();
                  }
                }}
              />
            </div>
            <CommandList>
              {availableOptions.filter((s) => s.toLowerCase().includes(inputValue.toLowerCase()))
                .length === 0 &&
                !showCustomOption && (
                  <div className="py-6 text-center text-sm">
                    No skills found. Type to add a custom skill.
                  </div>
                )}
              <CommandGroup>
                {showCustomOption && (
                  <CommandItem
                    onSelect={() => handleSelect(inputValue.trim())}
                    className="cursor-pointer bg-primary/10 text-primary font-medium"
                  >
                    <Plus className="mr-2 h-4 w-4" /> Add "{inputValue.trim()}"
                  </CommandItem>
                )}
                {availableOptions
                  .filter((s) => s.toLowerCase().includes(inputValue.toLowerCase()))
                  .slice(0, 15) // max 15 to keep it clean
                  .map((skill) => (
                    <CommandItem
                      key={skill}
                      onSelect={() => handleSelect(skill)}
                      className="cursor-pointer"
                    >
                      {skill}
                    </CommandItem>
                  ))}
              </CommandGroup>
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
    </div>
  );
}
