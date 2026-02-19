import { useEffect, useState } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { LoyaltyCard } from '@/components/LoyaltyCard';
import { Button } from '@/components/ui/button';
import { 
  CheckCircle, 
  Home, 
  Printer,
  PartyPopper,
  Sparkles
} from 'lucide-react';

interface LocationState {
  loyaltyNumber: string;
  customerName: string;
}

export default function RegisterSuccess() {
  const location = useLocation();
  const navigate = useNavigate();
  const [showConfetti, setShowConfetti] = useState(true);
  
  const state = location.state as LocationState | null;

  useEffect(() => {
    // Redirect if no loyalty number in state
    if (!state?.loyaltyNumber) {
      navigate('/register');
      return;
    }

    // Hide confetti after animation
    const timer = setTimeout(() => setShowConfetti(false), 3000);
    return () => clearTimeout(timer);
  }, [state, navigate]);

  if (!state?.loyaltyNumber) {
    return null;
  }

  const handlePrint = () => {
    window.print();
  };

  return (
    <Layout>
      {/* Confetti Animation */}
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute animate-confetti"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 2}s`,
                backgroundColor: ['#db2777', '#a855f7', '#0ea5e9', '#22c55e'][Math.floor(Math.random() * 4)],
                width: '10px',
                height: '10px',
                borderRadius: '2px',
                top: '-20px',
              }}
            />
          ))}
        </div>
      )}

      <div className="min-h-[calc(100vh-4rem)] py-12 md:py-20 bg-muted">
        <div className="container px-4 md:px-6">
          <div className="max-w-lg mx-auto text-center">
            {/* Success Icon */}
            <div className="relative inline-flex items-center justify-center mb-6">
              <div className="absolute inset-0 bg-green-500/20 rounded-full blur-xl animate-pulse" />
              <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-green-500 shadow-lg animate-bounce-in">
                <CheckCircle className="h-10 w-10 text-white" />
              </div>
            </div>

            {/* Header */}
            <div className="mb-8 animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="flex items-center justify-center gap-2 mb-3">
                <PartyPopper className="h-6 w-6 text-pink" />
                <span className="text-lg font-semibold text-pink">Congratulations!</span>
                <PartyPopper className="h-6 w-6 text-pink transform scale-x-[-1]" />
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-3">
                Registration Successful
              </h1>
              <p className="text-muted-foreground">
                Welcome to the Singha Super family, {state.customerName}!
              </p>
            </div>

            {/* Loyalty Card */}
            <div className="mb-8 animate-scale-in" style={{ animationDelay: '0.4s' }}>
              <LoyaltyCard 
                loyaltyNumber={state.loyaltyNumber} 
                customerName={state.customerName}
              />
            </div>

            {/* Instructions */}
            <div className="bg-card rounded-2xl p-6 shadow-lg border border-border mb-8 text-left animate-fade-in" style={{ animationDelay: '0.6s' }}>
              <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-accent" />
                How to use your loyalty number
              </h3>
              <ol className="space-y-3 text-sm text-muted-foreground">
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-xs font-bold flex-shrink-0">1</span>
                  <span>Remember or save your 4-digit loyalty number: <strong className="text-foreground">{state.loyaltyNumber}</strong></span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-xs font-bold flex-shrink-0">2</span>
                  <span>Visit Singha Super at Ja-Ela and shop as usual</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-xs font-bold flex-shrink-0">3</span>
                  <span>At billing, tell the cashier your loyalty number</span>
                </li>
                <li className="flex gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-secondary-foreground text-xs font-bold flex-shrink-0">4</span>
                  <span>Enjoy instant discounts on your purchase!</span>
                </li>
              </ol>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in" style={{ animationDelay: '0.8s' }}>
              <Button
                onClick={handlePrint}
                variant="outline"
                size="lg"
                className="border-border"
              >
                <Printer className="mr-2 h-5 w-5" />
                Print Card
              </Button>
              <Link to="/">
                <Button size="lg" className="gradient-hero text-primary-foreground hover:opacity-90">
                  <Home className="mr-2 h-5 w-5" />
                  Back to Home
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Print Styles */}
      <style>{`
        @media print {
          body * {
            visibility: hidden;
          }
          .loyalty-card, .loyalty-card * {
            visibility: visible;
          }
          .loyalty-card {
            position: absolute;
            left: 50%;
            top: 50%;
            transform: translate(-50%, -50%);
          }
        }
      `}</style>
    </Layout>
  );
}
