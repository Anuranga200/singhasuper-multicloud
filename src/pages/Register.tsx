import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  registerCustomer, 
  validateNIC, 
  validatePhoneNumber,
  type RegisterCustomerRequest 
} from '@/services/api';
import { 
  User, 
  CreditCard, 
  Phone, 
  AlertCircle, 
  Loader2,
  CheckCircle,
  Info
} from 'lucide-react';

interface FormErrors {
  nicNumber?: string;
  fullName?: string;
  phoneNumber?: string;
  general?: string;
}

export default function Register() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [formData, setFormData] = useState<RegisterCustomerRequest>({
    nicNumber: '',
    fullName: '',
    phoneNumber: '',
  });

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    // NIC validation
    if (!formData.nicNumber.trim()) {
      newErrors.nicNumber = 'NIC number is required';
    } else if (!validateNIC(formData.nicNumber.trim())) {
      newErrors.nicNumber = 'Invalid NIC format. Use old format (9 digits + V/X) or new format (12 digits)';
    }

    // Name validation
    if (!formData.fullName.trim()) {
      newErrors.fullName = 'Full name is required';
    } else if (formData.fullName.trim().length < 3) {
      newErrors.fullName = 'Name must be at least 3 characters';
    } else if (formData.fullName.trim().length > 100) {
      newErrors.fullName = 'Name must be less than 100 characters';
    }

    // Phone validation
    if (!formData.phoneNumber.trim()) {
      newErrors.phoneNumber = 'Phone number is required';
    } else if (!validatePhoneNumber(formData.phoneNumber.trim())) {
      newErrors.phoneNumber = 'Invalid phone format. Use 07XXXXXXXX or +947XXXXXXXX';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    setErrors({});

    try {
      const response = await registerCustomer({
        nicNumber: formData.nicNumber.trim(),
        fullName: formData.fullName.trim(),
        phoneNumber: formData.phoneNumber.trim(),
      });

      if (response.success && response.loyaltyNumber) {
        // Navigate to success page with loyalty number
        navigate('/register/success', {
          state: {
            loyaltyNumber: response.loyaltyNumber,
            customerName: formData.fullName.trim(),
          },
        });
      } else {
        setErrors({ general: response.error || 'Registration failed. Please try again.' });
      }
    } catch (error) {
      setErrors({ general: 'An unexpected error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof RegisterCustomerRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear field error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  return (
    <Layout>
      <div className="min-h-[calc(100vh-4rem)] py-12 md:py-20 bg-muted">
        <div className="container px-4 md:px-6">
          <div className="max-w-lg mx-auto">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-3">
                Join Our Loyalty Program
              </h1>
              <p className="text-muted-foreground">
                Register once, save forever. Get your unique 4-digit loyalty number.
              </p>
            </div>

            {/* Form Card */}
            <div className="bg-card rounded-2xl shadow-xl border border-border p-6 md:p-8">
              <form onSubmit={handleSubmit} className="space-y-6">
                {/* General Error */}
                {errors.general && (
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/30">
                    <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-destructive">{errors.general}</p>
                  </div>
                )}

                {/* NIC Number */}
                <div className="space-y-2">
                  <Label htmlFor="nicNumber" className="text-foreground font-medium">
                    National ID Number (NIC)
                  </Label>
                  <div className="relative">
                    <CreditCard className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                      id="nicNumber"
                      type="text"
                      placeholder="e.g., 199012345678 or 901234567V"
                      value={formData.nicNumber}
                      onChange={(e) => handleInputChange('nicNumber', e.target.value)}
                      className={`pl-10 h-12 ${errors.nicNumber ? 'border-destructive focus-visible:ring-destructive' : ''}`}
                      disabled={isLoading}
                    />
                  </div>
                  {errors.nicNumber && (
                    <p className="text-sm text-destructive flex items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      {errors.nicNumber}
                    </p>
                  )}
                </div>

                {/* Full Name */}
                <div className="space-y-2">
                  <Label htmlFor="fullName" className="text-foreground font-medium">
                    Full Name
                  </Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                      id="fullName"
                      type="text"
                      placeholder="Enter your full name"
                      value={formData.fullName}
                      onChange={(e) => handleInputChange('fullName', e.target.value)}
                      className={`pl-10 h-12 ${errors.fullName ? 'border-destructive focus-visible:ring-destructive' : ''}`}
                      disabled={isLoading}
                    />
                  </div>
                  {errors.fullName && (
                    <p className="text-sm text-destructive flex items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      {errors.fullName}
                    </p>
                  )}
                </div>

                {/* Phone Number */}
                <div className="space-y-2">
                  <Label htmlFor="phoneNumber" className="text-foreground font-medium">
                    Phone Number
                  </Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                      id="phoneNumber"
                      type="tel"
                      placeholder="e.g., 0771234567"
                      value={formData.phoneNumber}
                      onChange={(e) => handleInputChange('phoneNumber', e.target.value)}
                      className={`pl-10 h-12 ${errors.phoneNumber ? 'border-destructive focus-visible:ring-destructive' : ''}`}
                      disabled={isLoading}
                    />
                  </div>
                  {errors.phoneNumber && (
                    <p className="text-sm text-destructive flex items-center gap-1">
                      <AlertCircle className="h-4 w-4" />
                      {errors.phoneNumber}
                    </p>
                  )}
                </div>

                {/* Info Box */}
                <div className="flex items-start gap-3 p-4 rounded-lg bg-secondary/10 border border-secondary/30">
                  <Info className="h-5 w-5 text-secondary flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-muted-foreground">
                    <p className="font-medium text-foreground mb-1">How it works:</p>
                    <ul className="space-y-1 list-disc list-inside">
                      <li>Register once with your NIC and phone number</li>
                      <li>Receive a unique 4-digit loyalty number</li>
                      <li>Show your number at billing to get discounts</li>
                    </ul>
                  </div>
                </div>

                {/* Submit Button */}
                <Button
                  type="submit"
                  className="w-full h-12 gradient-accent text-primary-foreground hover:opacity-90 transition-opacity shadow-accent text-base font-semibold"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Registering...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="mr-2 h-5 w-5" />
                      Register & Get Loyalty Number
                    </>
                  )}
                </Button>

                {/* Terms */}
                <p className="text-xs text-center text-muted-foreground">
                  By registering, you agree to our{' '}
                  <a href="/terms" className="text-secondary hover:underline">Terms</a>
                  {' '}and{' '}
                  <a href="/privacy" className="text-secondary hover:underline">Privacy Policy</a>.
                </p>
              </form>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
