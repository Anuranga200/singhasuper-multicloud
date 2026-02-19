import { Link } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { 
  Percent, 
  Users, 
  BadgeCheck, 
  MapPin, 
  ArrowRight,
  Sparkles,
  Tag,
  Heart
} from 'lucide-react';

export default function Home() {
  return (
    <Layout>
      {/* Hero Section */}
      <section className="relative overflow-hidden gradient-hero py-20 md:py-32">
        {/* Decorative elements */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-20 left-10 w-64 h-64 bg-secondary/20 rounded-full blur-3xl" />
          <div className="absolute bottom-10 right-10 w-96 h-96 bg-accent/10 rounded-full blur-3xl" />
        </div>

        <div className="container relative px-4 md:px-6">
          <div className="flex flex-col items-center text-center space-y-8">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-foreground/10 border border-primary-foreground/20 animate-fade-in">
              <Sparkles className="h-4 w-4 text-pink" />
              <span className="text-sm font-medium text-primary-foreground">
                Ja-Ela's #1 Discount Supermarket
              </span>
            </div>

            {/* Headline */}
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-primary-foreground max-w-4xl leading-tight animate-slide-up">
              Save Your Salary,{' '}
              <span className="text-gradient bg-gradient-to-r from-pink to-purple bg-clip-text text-transparent">
                Shop Smart
              </span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-primary-foreground/80 max-w-2xl animate-slide-up" style={{ animationDelay: '0.1s' }}>
              Extreme discounts on over 80% of our products. Join our loyalty program 
              and start saving from your very first visit.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 animate-slide-up" style={{ animationDelay: '0.2s' }}>
              <Link to="/register">
                <Button size="lg" className="gradient-accent text-primary-foreground hover:opacity-90 transition-opacity shadow-accent text-base px-8 py-6">
                  Register as Loyalty Customer
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <a href="#location">
                <Button size="lg" variant="outline" className="bg-primary-foreground/10 text-primary-foreground border-primary-foreground/30 hover:bg-primary-foreground/20 text-base px-8 py-6">
                  <MapPin className="mr-2 h-5 w-5" />
                  Visit Our Store
                </Button>
              </a>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-8 pt-8 animate-fade-in" style={{ animationDelay: '0.3s' }}>
              <div className="text-center">
                <p className="text-3xl md:text-4xl font-bold text-primary-foreground">80%+</p>
                <p className="text-sm text-primary-foreground/60">Products Discounted</p>
              </div>
              <div className="text-center">
                <p className="text-3xl md:text-4xl font-bold text-primary-foreground">1000+</p>
                <p className="text-sm text-primary-foreground/60">Happy Customers</p>
              </div>
              <div className="text-center">
                <p className="text-3xl md:text-4xl font-bold text-primary-foreground">Daily</p>
                <p className="text-sm text-primary-foreground/60">Fresh Arrivals</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-background">
        <div className="container px-4 md:px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Why Choose Singha Super?
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              We're not just a supermarket – we're your partner in smart shopping
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="group relative bg-card rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow border border-border">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl gradient-accent mb-6 shadow-accent">
                <Percent className="h-7 w-7 text-primary-foreground" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-3">
                Extreme Discounts
              </h3>
              <p className="text-muted-foreground">
                Over 80% of our products are heavily discounted. Save more on every visit 
                without compromising on quality.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="group relative bg-card rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow border border-border">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl gradient-success mb-6 shadow-glow">
                <BadgeCheck className="h-7 w-7 text-primary-foreground" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-3">
                Loyalty Program
              </h3>
              <p className="text-muted-foreground">
                Register once and get your unique 4-digit loyalty number. 
                Enjoy exclusive discounts at every checkout.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="group relative bg-card rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow border border-border">
              <div className="flex h-14 w-14 items-center justify-center rounded-xl gradient-hero mb-6">
                <Heart className="h-7 w-7 text-primary-foreground" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-3">
                Community First
              </h3>
              <p className="text-muted-foreground">
                Proudly serving Ja-Ela and surrounding areas. 
                We're your trusted neighborhood supermarket.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-muted">
        <div className="container px-4 md:px-6">
          <div className="relative overflow-hidden rounded-3xl gradient-accent p-8 md:p-12 lg:p-16">
            {/* Decorative */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary-foreground/10 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-primary-foreground/10 rounded-full translate-y-1/2 -translate-x-1/2" />
            
            <div className="relative flex flex-col lg:flex-row items-center justify-between gap-8">
              <div className="text-center lg:text-left">
                <div className="flex items-center justify-center lg:justify-start gap-2 mb-4">
                  <Tag className="h-6 w-6 text-primary-foreground" />
                  <span className="text-primary-foreground/80 font-medium">
                    Join Today
                  </span>
                </div>
                <h2 className="text-3xl md:text-4xl font-bold text-primary-foreground mb-4">
                  Start Saving Now
                </h2>
                <p className="text-primary-foreground/80 max-w-lg">
                  Register as a loyalty customer and receive your unique 4-digit number. 
                  Show it at billing and enjoy instant discounts on every purchase.
                </p>
              </div>
              <Link to="/register">
                <Button size="lg" className="bg-primary-foreground text-primary hover:bg-primary-foreground/90 text-base px-8 py-6 shadow-xl">
                  <Users className="mr-2 h-5 w-5" />
                  Register as Loyalty Customer
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Location Section */}
      <section id="location" className="py-20 bg-background">
        <div className="container px-4 md:px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Visit Our Store
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Conveniently located in the heart of Ja-Ela, we're easy to find and always ready to serve you
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-8 items-start">
            {/* Map */}
            <div className="rounded-2xl overflow-hidden shadow-lg border border-border h-[400px]">
              <iframe
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d31675.90164618!2d79.87!3d7.07!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3ae2f9c71a8d7c6d%3A0x9c44f0ed5d3a3b1a!2sJa-Ela%2C%20Sri%20Lanka!5e0!3m2!1sen!2sus!4v1234567890"
                width="100%"
                height="100%"
                style={{ border: 0 }}
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                title="Singha Super Location"
              />
            </div>

            {/* Store Info */}
            <div className="space-y-6">
              <div className="bg-card rounded-2xl p-6 shadow-lg border border-border">
                <h3 className="text-xl font-semibold text-foreground mb-4 flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-secondary" />
                  Store Address
                </h3>
                <p className="text-muted-foreground mb-4">
                  Main Street, Ja-Ela,<br />
                  Gampaha District,<br />
                  Western Province, Sri Lanka
                </p>
                <a
                  href="https://maps.google.com/?q=Ja-Ela,Sri+Lanka"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-secondary hover:text-secondary/80 font-medium"
                >
                  Get Directions
                  <ArrowRight className="ml-1 h-4 w-4" />
                </a>
              </div>

              <div className="bg-card rounded-2xl p-6 shadow-lg border border-border">
                <h3 className="text-xl font-semibold text-foreground mb-4">
                  Store Hours
                </h3>
                <div className="space-y-2 text-muted-foreground">
                  <div className="flex justify-between">
                    <span>Monday - Saturday</span>
                    <span className="font-medium text-foreground">9:00 AM - 9:00 PM</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Sunday</span>
                    <span className="font-medium text-foreground">9:00 AM - 8:00 PM</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Poya Days</span>
                    <span className="font-medium text-foreground">CLOSED</span>
                  </div>
                </div>
              </div>

              <div className="bg-card rounded-2xl p-6 shadow-lg border border-border">
                <h3 className="text-xl font-semibold text-foreground mb-4">
                  Contact Us
                </h3>
                <div className="space-y-2 text-muted-foreground">
                  <p>Phone: <span className="font-medium text-foreground">+94 74 100 2009</span></p>
                  <p>Email: <span className="font-medium text-foreground">1singhasuper@gmail.com</span></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
}
