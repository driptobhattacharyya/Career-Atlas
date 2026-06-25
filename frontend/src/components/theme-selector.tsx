import { Sun, Moon, Waves, Flame, Palette } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useTheme } from "@/context/theme-context";

export function ThemeSelector() {
  const { theme, setTheme } = useTheme();

  const getIcon = () => {
    switch (theme) {
      case "light": return <Sun className="h-[1.2rem] w-[1.2rem]" />;
      case "dark": return <Moon className="h-[1.2rem] w-[1.2rem]" />;
      case "theme-ocean": return <Waves className="h-[1.2rem] w-[1.2rem] text-blue-500" />;
      case "theme-sunset": return <Flame className="h-[1.2rem] w-[1.2rem] text-orange-500" />;
      default: return <Palette className="h-[1.2rem] w-[1.2rem]" />;
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" className="h-9 w-9 rounded-full focus-visible:ring-0">
          {getIcon()}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="rounded-xl">
        <DropdownMenuItem onClick={() => setTheme("light")} className="gap-2 cursor-pointer rounded-lg">
          <Sun className="h-4 w-4" />
          <span>Light</span>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("dark")} className="gap-2 cursor-pointer rounded-lg">
          <Moon className="h-4 w-4" />
          <span>Dark</span>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("theme-ocean")} className="gap-2 cursor-pointer rounded-lg">
          <div className="flex h-4 w-4 items-center justify-center rounded-full bg-blue-500">
            <Waves className="h-3 w-3 text-white" />
          </div>
          <span>Ocean</span>
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("theme-sunset")} className="gap-2 cursor-pointer rounded-lg">
          <div className="flex h-4 w-4 items-center justify-center rounded-full bg-orange-500">
            <Flame className="h-3 w-3 text-white" />
          </div>
          <span>Sunset</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
