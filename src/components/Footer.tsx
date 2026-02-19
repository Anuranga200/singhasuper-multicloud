import { Link } from 'react-router-dom';
import { ShoppingCart, MapPin, Phone, Clock, Lock } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-primary text-primary-foreground">
      <div className="container px-4 md:px-6 py-12">
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-foreground/20">
                <ShoppingCart className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-lg">Singha Super</h3>
                <p className="text-xs text-primary-foreground/70">Save your salary</p>
              </div>
            </div>
            <p className="text-sm text-primary-foreground/80 leading-relaxed">
              Your trusted neighborhood supermarket in Ja-Ela, offering extreme discounts 
              on over 80% of our products. Quality you can trust, prices you'll love.
            </p>
          </div>

          {/* Location */}
          <div className="space-y-4">
            <h4 className="font-semibold text-base">Visit Us</h4>
            <div className="space-y-3 text-sm text-primary-foreground/80">
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Main Street, Ja-Ela, Sri Lanka</span>
              </div>
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 flex-shrink-0" />
                <span>+94 11 234 5678</span>
              </div>
              <div className="flex items-start gap-2">
                <Clock className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <div>
                  <p>Mon - Sat: 8:00 AM - 9:00 PM</p>
                  <p>Sunday: 9:00 AM - 6:00 PM</p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Links */}
          <div className="space-y-4">
            <h4 className="font-semibold text-base">Quick Links</h4>
            <nav className="flex flex-col gap-2 text-sm">
              <Link to="/" className="text-primary-foreground/80 hover:text-primary-foreground transition-colors">
                Home
              </Link>
              <Link to="/register" className="text-primary-foreground/80 hover:text-primary-foreground transition-colors">
                Join Loyalty Program
              </Link>
              <Link to="/privacy" className="text-primary-foreground/80 hover:text-primary-foreground transition-colors">
                Privacy Policy
              </Link>
              <Link to="/terms" className="text-primary-foreground/80 hover:text-primary-foreground transition-colors">
                Terms & Conditions
              </Link>
            </nav>
          </div>

          {/* Loyalty */}
          <div className="space-y-4">
            <h4 className="font-semibold text-base">Loyalty Program</h4>
            <p className="text-sm text-primary-foreground/80">
              Register once, save forever! Get your unique 4-digit loyalty number 
              and enjoy exclusive discounts on every visit.
            </p>
            <Link
              to="/register"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-foreground text-primary font-medium text-sm hover:bg-primary-foreground/90 transition-colors"
            >
              Register Now
            </Link>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-6 border-t border-primary-foreground/20 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-sm text-primary-foreground/60">
            © {new Date().getFullYear()} Singha Super. All rights reserved.
          </p>
          <Link
            to="/admin"
            className="flex items-center gap-1 text-xs text-primary-foreground/40 hover:text-primary-foreground/60 transition-colors"
          >
            <Lock className="h-3 w-3" />
            Admin
          </Link>
        </div>
      </div>
    </footer>
  );
}
