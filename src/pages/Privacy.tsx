import { Layout } from '@/components/Layout';
import { Shield, Lock, Eye, Database, UserCheck, Mail } from 'lucide-react';

export default function Privacy() {
  return (
    <Layout>
      <div className="py-12 md:py-20 bg-background">
        <div className="container px-4 md:px-6 max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl gradient-hero mb-6">
              <Shield className="h-8 w-8 text-primary-foreground" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Privacy Policy
            </h1>
            <p className="text-muted-foreground">
              Last updated: January 2024
            </p>
          </div>

          {/* Content */}
          <div className="prose prose-lg max-w-none">
            <div className="bg-card rounded-2xl p-6 md:p-8 shadow-lg border border-border space-y-8">
              
              <section>
                <div className="flex items-center gap-3 mb-4">
                  <Eye className="h-6 w-6 text-secondary" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Information We Collect
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  When you register for our loyalty program, we collect the following personal information:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                  <li>National Identity Card (NIC) number for identification</li>
                  <li>Full name as it appears on your NIC</li>
                  <li>Mobile phone number for communication</li>
                </ul>
              </section>

              <section>
                <div className="flex items-center gap-3 mb-4">
                  <Database className="h-6 w-6 text-secondary" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    How We Use Your Information
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  Your personal information is used solely for the following purposes:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                  <li>To create and maintain your loyalty account</li>
                  <li>To verify your identity at checkout</li>
                  <li>To apply loyalty discounts to your purchases</li>
                  <li>To contact you regarding important updates about our services</li>
                </ul>
              </section>

              <section>
                <div className="flex items-center gap-3 mb-4">
                  <Lock className="h-6 w-6 text-secondary" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Data Security
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  We implement appropriate security measures to protect your personal information 
                  against unauthorized access, alteration, disclosure, or destruction. Your data 
                  is stored securely and access is restricted to authorized personnel only.
                </p>
              </section>

              <section>
                <div className="flex items-center gap-3 mb-4">
                  <UserCheck className="h-6 w-6 text-secondary" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Your Rights
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  You have the right to:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                  <li>Access your personal data we hold</li>
                  <li>Request correction of inaccurate data</li>
                  <li>Request deletion of your data (subject to legal requirements)</li>
                  <li>Opt-out of promotional communications</li>
                </ul>
              </section>

              <section>
                <div className="flex items-center gap-3 mb-4">
                  <Mail className="h-6 w-6 text-secondary" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Contact Us
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  If you have any questions about this Privacy Policy or wish to exercise your 
                  rights, please contact us at:
                </p>
                <div className="bg-muted rounded-lg p-4 mt-4">
                  <p className="text-foreground font-medium">Singha Super</p>
                  <p className="text-muted-foreground">Main Street, Ja-Ela, Sri Lanka</p>
                  <p className="text-muted-foreground">Phone: +94 11 234 5678</p>
                  <p className="text-muted-foreground">Email: privacy@singhasuper.lk</p>
                </div>
              </section>

              <section className="pt-6 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  This privacy policy may be updated from time to time. We will notify you of 
                  any significant changes by posting the new policy on our website. Your 
                  continued use of our services after such changes constitutes acceptance of 
                  the updated policy.
                </p>
              </section>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
