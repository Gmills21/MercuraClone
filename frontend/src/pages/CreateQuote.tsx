import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Upload, FileText, Mail, Loader2, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { uploadApi, quotesApi } from '@/services/api';
import { toast } from 'sonner';

interface RecentQuote {
  id: string;
  quote_number: string;
  customer?: string;
  status: string;
  total_amount: number;
  margin_added?: number;
  created_at?: string;
}

export const CreateQuote = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recentQuotes, setRecentQuotes] = useState<RecentQuote[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Fetch recent quotes on mount
  useEffect(() => {
    fetchRecentQuotes();
  }, []);

  const fetchRecentQuotes = async () => {
    try {
      const response = await quotesApi.list(10);
      const quotes = response.data.map((quote: any) => ({
        id: quote.id,
        quote_number: quote.quote_number,
        customer: quote.customer_name || quote.customers?.name || 'Unknown Customer',
        status: quote.status,
        total_amount: quote.total_amount || 0,
        margin_added: quote.metadata?.total_margin_added || 0,
        created_at: quote.created_at,
      }));
      setRecentQuotes(quotes);
    } catch (error) {
      console.error('Error fetching recent quotes:', error);
    }
  };

  const handleFileUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const file = fileArray[0]; // Process first file

    if (!file) return;

    // Validate file type
    const validTypes = [
      'application/pdf',
      'image/png',
      'image/jpeg',
      'image/jpg',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
      'text/csv',
    ];

    const validExtensions = ['.pdf', '.png', '.jpg', '.jpeg', '.png', '.xlsx', '.xls', '.csv'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

    if (
      !validTypes.includes(file.type) &&
      !validExtensions.some((ext) => file.name.toLowerCase().endsWith(ext))
    ) {
      toast.error('Invalid file type', {
        description: 'Please upload a PDF, image (PNG/JPG), or spreadsheet (CSV/Excel)',
      });
      return;
    }

    setIsProcessing(true);

    try {
      const response = await uploadApi.upload(file);
      const data = response.data;

      // Show "Aha Moment" toast with margin improvements
      if (data.total_margin_added > 0) {
        const topImprovement = data.margin_improvements?.[0];
        if (topImprovement) {
          toast.success(`Margin Added: $${data.total_margin_added.toFixed(2)}`, {
            description: `Swapped ${topImprovement.original_sku || 'Competitor SKU'} for High-Margin SKU ${topImprovement.suggested_sku}`,
            duration: 6000,
          });
        } else {
          toast.success(`Margin Added: $${data.total_margin_added.toFixed(2)}`, {
            description: 'Optimized SKU matching increased quote profitability',
            duration: 6000,
          });
        }

        // Show additional improvements if any
        if (data.margin_improvements && data.margin_improvements.length > 1) {
          const additionalCount = data.margin_improvements.length - 1;
          setTimeout(() => {
            toast.info(`${additionalCount} more optimization${additionalCount > 1 ? 's' : ''} applied`, {
              description: 'View quote details to see all margin improvements',
            });
          }, 2000);
        }
      } else {
        toast.success('Extraction completed', {
          description: `Extracted ${data.items_extracted} line items from ${file.name}`,
        });
      }

      // Refresh recent quotes
      await fetchRecentQuotes();

      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      console.error('Upload error:', error);
      toast.error('Upload failed', {
        description: error.response?.data?.detail || error.message || 'Failed to process file',
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragging(false);

      if (isProcessing) return;

      const files = e.dataTransfer.files;
      if (files.length > 0) {
        handleFileUpload(files);
      }
    },
    [isProcessing]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files && e.target.files.length > 0 && !isProcessing) {
        handleFileUpload(e.target.files);
      }
    },
    [isProcessing]
  );

  const handleClick = useCallback(() => {
    if (!isProcessing && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [isProcessing]);

  const getStatusVariant = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'draft':
        return 'secondary';
      case 'processing':
        return 'default';
      case 'sent':
        return 'default';
      default:
        return 'secondary';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Universal Intake</h1>
        <p className="text-muted-foreground mt-2">
          Drop messy PDFs, emails, or napkin sketches here to automatically create quotes
        </p>
      </div>

      {/* Drop Zone */}
      <Card
        className={`border-2 border-dashed transition-all duration-200 cursor-pointer ${
          isDragging
            ? 'border-primary bg-primary/5 scale-[1.02]'
            : isProcessing
            ? 'border-muted-foreground/25 opacity-50 cursor-not-allowed'
            : 'border-muted-foreground/25 hover:border-muted-foreground/50'
        }`}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <CardContent className="flex flex-col items-center justify-center py-16 px-6">
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            accept=".pdf,.png,.jpg,.jpeg,.xlsx,.xls,.csv"
            onChange={handleFileInputChange}
            disabled={isProcessing}
          />
          <div className="flex flex-col items-center gap-4 text-center">
            {isProcessing ? (
              <>
                <div className="rounded-full bg-primary/10 p-6">
                  <Loader2 className="h-12 w-12 text-primary animate-spin" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">Processing...</h3>
                  <p className="text-muted-foreground max-w-md">
                    Extracting data and optimizing margins. This may take a few moments.
                  </p>
                </div>
              </>
            ) : (
              <>
                <div className="rounded-full bg-primary/10 p-6">
                  <Upload className="h-12 w-12 text-primary" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold">
                    Drop Messy PDF, Email, or Napkin Sketch Here
                  </h3>
                  <p className="text-muted-foreground max-w-md">
                    Drag and drop your files here, or click to browse. We'll extract the relevant
                    information, match SKUs, and optimize margins automatically.
                  </p>
                </div>
                <div className="flex items-center gap-4 mt-4">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <FileText className="h-4 w-4" />
                    <span>PDF Files</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Mail className="h-4 w-4" />
                    <span>Email Attachments</span>
                  </div>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Recent Extractions */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Extractions</CardTitle>
          <CardDescription>
            Your recently created quotes from uploaded documents with margin optimizations
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recentQuotes.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No recent extractions. Upload a file to get started.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead className="text-right">Margin Added</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentQuotes.map((quote) => (
                  <TableRow key={quote.id}>
                    <TableCell className="font-medium">{quote.customer}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusVariant(quote.status)}>
                        {quote.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right font-semibold">
                      {formatCurrency(quote.total_amount)}
                    </TableCell>
                    <TableCell className="text-right">
                      {quote.margin_added && quote.margin_added > 0 ? (
                        <div className="flex items-center justify-end gap-1 text-green-500 font-semibold">
                          <TrendingUp className="h-4 w-4" />
                          <span>+{formatCurrency(quote.margin_added)}</span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default CreateQuote;
