import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps {
  className?: string;
}

export function Spinner({ className = "h-8 w-8" }: SpinnerProps) {
  return (
    <div className="flex justify-center items-center p-8">
      <Loader2 className={cn(className, "animate-spin text-primary")} />
    </div>
  );
}
