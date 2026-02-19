import { ShoppingCart, Sparkles } from 'lucide-react';

interface LoyaltyCardProps {
  loyaltyNumber: string;
  customerName?: string;
}

export function LoyaltyCard({ loyaltyNumber, customerName }: LoyaltyCardProps) {
  return (
    <div className="relative w-full max-w-sm mx-auto">
      {/* Glow effect */}
      <div className="absolute inset-0 blur-2xl opacity-40 gradient-accent rounded-3xl" />
      
      {/* Card */}
      <div className="relative gradient-hero rounded-2xl p-6 shadow-xl overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary-foreground/5 rounded-full -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-24 h-24 bg-primary-foreground/5 rounded-full translate-y-1/2 -translate-x-1/2" />
        
        {/* Content */}
        <div className="relative space-y-4">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-foreground/20">
                <ShoppingCart className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="text-primary-foreground/80 text-sm font-medium">
                Singha Super
              </span>
            </div>
            <Sparkles className="h-5 w-5 text-pink animate-pulse" />
          </div>

          {/* Loyalty Number */}
          <div className="py-4">
            <p className="text-primary-foreground/60 text-xs uppercase tracking-wider mb-2">
              Loyalty Number
            </p>
            <div className="flex items-center justify-center gap-3">
              {loyaltyNumber.split('').map((digit, index) => (
                <span
                  key={index}
                  className="flex items-center justify-center w-14 h-16 bg-primary-foreground/10 rounded-xl text-3xl font-bold text-primary-foreground border border-primary-foreground/20"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  {digit}
                </span>
              ))}
            </div>
          </div>

          {/* Customer Name */}
          {customerName && (
            <div className="pt-2 border-t border-primary-foreground/10">
              <p className="text-primary-foreground/60 text-xs uppercase tracking-wider mb-1">
                Member Name
              </p>
              <p className="text-primary-foreground font-medium truncate">
                {customerName}
              </p>
            </div>
          )}

          {/* Tagline */}
          <div className="flex items-center justify-center pt-2">
            <span className="text-gradient text-sm font-semibold bg-gradient-to-r from-pink to-purple text-transparent bg-clip-text">
              Save your salary
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
