import { Layout } from '@/components/Layout';
import { FileText, Users, CreditCard, AlertTriangle, Scale, BookOpen } from 'lucide-react';

export default function Terms() {
  return (
    <Layout>
      <div className="py-12 md:py-20 bg-background">
        <div className="container px-4 md:px-6 max-w-4xl">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center h-16 w-16 rounded-2xl gradient-accent mb-6">
              <FileText className="h-8 w-8 text-primary-foreground" />
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
              Terms & Conditions
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
                  <BookOpen className="h-6 w-6 text-accent" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Introduction
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  Welcome to Singha Super's Loyalty Program. By registering for our program, 
                  you agree to be bound by these Terms and Conditions. Please read them carefully 
                  before completing your registration.
                </p>
              </section>

              <section>
                <div className="flex items-center gap-3 mb-4">
                  <Users className="h-6 w-6 text-accent" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Eligibility
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  To register for our loyalty program, you must:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                  <li>Be at least 18 years of age</li>
                  <li>Hold a valid Sri Lankan National Identity Card (NIC)</li>
                  <li>Provide accurate and truthful information during registration</li>
                  <li>Have a valid Sri Lankan mobile phone number</li>
                </ul>
              </section>

              <section>
                <div className="flex items-center gap-3 mb-4">
                  <CreditCard className="h-6 w-6 text-accent" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Loyalty Number
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  Upon successful registration, you will receive a unique 4-digit loyalty number. 
                  This number:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                  <li>Is personal and non-transferable</li>
                  <li>Must be presented at checkout to receive discounts</li>
                  <li>May be used only by the registered member</li>
                  <li>Cannot be duplicated or replaced once issued</li>
                </ul>
              </section>

              <section>
                <div className="flex items-center gap-3 mb-4">
                  <Scale className="h-6 w-6 text-accent" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Program Benefits
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  As a loyalty member, you are entitled to:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                  <li>Exclusive discounts on selected products</li>
                  <li>Access to member-only promotions</li>
                  <li>Special offers during festive seasons</li>
                </ul>
                <p className="text-muted-foreground leading-relaxed mt-4">
                  Singha Super reserves the right to modify, suspend, or discontinue any 
                  benefits at any time without prior notice.
                </p>
              </section>

              <section>
                <div className="flex items-center gap-3 mb-4">
                  <AlertTriangle className="h-6 w-6 text-accent" />
                  <h2 className="text-xl font-semibold text-foreground m-0">
                    Restrictions
                  </h2>
                </div>
                <p className="text-muted-foreground leading-relaxed">
                  Members must not:
                </p>
                <ul className="list-disc list-inside text-muted-foreground space-y-2 ml-4">
                  <li>Share their loyalty number with others</li>
                  <li>Use false or misleading information during registration</li>
                  <li>Register multiple accounts using different identities</li>
                  <li>Attempt to manipulate or abuse the loyalty program</li>
                </ul>
                <p className="text-muted-foreground leading-relaxed mt-4">
                  Violation of these terms may result in immediate termination of membership 
                  and forfeiture of all benefits.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground mb-4">
                  Limitation of Liability
                </h2>
                <p className="text-muted-foreground leading-relaxed">
                  Singha Super shall not be liable for any indirect, incidental, or consequential 
                  damages arising from your participation in the loyalty program. Our total 
                  liability shall not exceed the value of discounts provided to you during 
                  your membership.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground mb-4">
                  Changes to Terms
                </h2>
                <p className="text-muted-foreground leading-relaxed">
                  Singha Super reserves the right to modify these Terms and Conditions at any 
                  time. Changes will be effective immediately upon posting on our website. 
                  Continued use of your loyalty membership after such changes constitutes 
                  acceptance of the modified terms.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-semibold text-foreground mb-4">
                  Governing Law
                </h2>
                <p className="text-muted-foreground leading-relaxed">
                  These Terms and Conditions shall be governed by and construed in accordance 
                  with the laws of Sri Lanka. Any disputes arising from these terms shall be 
                  subject to the exclusive jurisdiction of the courts of Sri Lanka.
                </p>
              </section>

              <section className="pt-6 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  By completing your registration, you acknowledge that you have read, 
                  understood, and agree to be bound by these Terms and Conditions.
                </p>
              </section>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
