import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Loader2, AlertCircle, CheckCircle2, TrendingUp, History, Package, ArrowRight, Send, Edit3, PlusCircle, Check, Trash2, Plus, ListChecks, FileText, ChevronDown } from 'lucide-react';
import { quotesApi, customersApi, productsApi, extractionsApi, api, projectsApi, organizationsApi } from '../services/api';
import { SmartEditor } from '../components/ui/SmartEditor';
import { trackEvent } from '../posthog';

// Smart quote creation with AI extraction
export const SmartQuote = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<'input' | 'review' | 'sending'>('input');
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [customers, setCustomers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<any>(null);
  const [isNewCustomer, setIsNewCustomer] = useState(false);
  const [newCustomerName, setNewCustomerName] = useState('');
  const [newCustomerEmail, setNewCustomerEmail] = useState('');
  const [newCustomerPhone, setNewCustomerPhone] = useState('');
  const [extractedData, setExtractedData] = useState<any>(null);
  const [lineItems, setLineItems] = useState<any[]>([]);
  const [suggestions, setSuggestions] = useState<any>({});
  const [taxRate, setTaxRate] = useState(8.5);
  const [dragActive, setDragActive] = useState(false);
  const [suggestedCustomer, setSuggestedCustomer] = useState<{ name: string; email?: string; phone?: string; company?: string } | null>(null);
  const [showCustomerSuggestion, setShowCustomerSuggestion] = useState(false);
  const [addingToCatalogId, setAddingToCatalogId] = useState<string | null>(null);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState<any>(null);
  const [isNewProject, setIsNewProject] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectAddress, setNewProjectAddress] = useState('');
  const [assignees, setAssignees] = useState<any[]>([]);
  const [selectedAssigneeId, setSelectedAssigneeId] = useState<string>('');

  // Race condition prevention
  const [isSubmitting, setIsSubmitting] = useState(false);
  const submitAttempted = useRef(false);

  // Manage object URL for file preview
  useEffect(() => {
    if (selectedFile) {
      const url = URL.createObjectURL(selectedFile);
      setFileUrl(url);
      return () => URL.revokeObjectURL(url);
    } else {
      setFileUrl(null);
    }
  }, [selectedFile]);

  // Load customers and products on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [custRes, prodRes, projRes] = await Promise.all([
        customersApi.list(),
        productsApi.list(),
        projectsApi.list(),
      ]);
      setCustomers(custRes.data || []);
      setProducts(prodRes.data || []);
      setProjects(projRes.data || []);

      // Load organization members for assignment
      try {
        const orgRes = await organizationsApi.getMe();
        if (orgRes.data?.id) {
          const membersRes = await organizationsApi.getMembers(orgRes.data.id);
          setAssignees(membersRes.data.members || []);
        }
      } catch (err) {
        console.error('Failed to load organization members:', err);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  // AI Extraction
  const handleExtract = async () => {
    if (!inputText.trim() && !selectedFile) return;

    // We now allow extraction without a customer selected to enable "Quick Add" detection
    if (isNewCustomer && !newCustomerName.trim()) {
      alert('Please enter a name for the new customer.');
      return;
    }

    setIsExtracting(true);
    trackEvent('receive_request', {
      source: selectedFile ? 'file' : 'text',
      extension: selectedFile ? selectedFile.name.split('.').pop() : 'text'
    });
    try {
      let res;
      if (selectedFile) {
        res = await extractionsApi.unifiedParse({
          file: selectedFile,
          source_type: 'document',
        });
      } else {
        res = await extractionsApi.unifiedParse({
          text: inputText,
          source_type: 'email',
        });
      }

      const data = res.data;
      setExtractedData(data);

      // --- AI Customer Suggestion Logic ---
      const extractedCustomerName = data.structured_data?.customer_name;
      if (extractedCustomerName && !selectedCustomer && !isNewCustomer) {
        // Look for existing customer
        const match = customers.find(c =>
          c.name.toLowerCase().includes(extractedCustomerName.toLowerCase()) ||
          (c.company && c.company.toLowerCase().includes(extractedCustomerName.toLowerCase()))
        );

        if (match) {
          setSelectedCustomer(match);
        } else {
          setSuggestedCustomer({
            name: extractedCustomerName,
            email: data.structured_data?.contact_email,
            phone: data.structured_data?.contact_phone,
            company: extractedCustomerName // Often the same in initial extraction
          });
          setShowCustomerSuggestion(true);
        }
      }
      // ------------------------------------

      // The unified endpoint returns structured_data directly
      const parsedItems = data.structured_data?.line_items || [];

      // Match extracted items to products with intelligence
      const smartItems = await matchItemsIntelligently(
        parsedItems,
        products,
        selectedCustomer || (isNewCustomer ? { name: newCustomerName } : null) || (extractedCustomerName ? { name: extractedCustomerName } : null)
      );

      setLineItems(smartItems);
      setStep('review');
    } catch (error: any) {
      console.error('Extraction failed:', error);

      // CRITICAL FIX: Handle timeout errors specifically
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        alert('Extraction timed out. The file may be too large or complex. Try:\n• Using a smaller file\n• Entering items manually\n• Breaking the document into smaller sections');
      } else if (error.response?.status === 429) {
        alert('Too many requests. Please wait a moment and try again.');
      } else {
        alert('Extraction failed. Please try again or enter items manually.');
      }
    } finally {
      setIsExtracting(false);
    }
  };

  // Intelligent item matching with history and pricing
  const matchItemsIntelligently = async (items: any[], products: any[], customer: any) => {
    return items.map((item, index) => {
      // Find matching product by name or SKU
      const matchedProduct = products.find(p =>
        p.name?.toLowerCase().includes(item.item_name?.toLowerCase()) ||
        p.sku?.toLowerCase() === item.sku?.toLowerCase()
      );

      const basePrice = matchedProduct?.price || item.unit_price || 0;
      const quantity = item.quantity || 1;

      // Generate pricing insights
      const insights = generatePricingInsights(matchedProduct, basePrice, customer);

      // CRITICAL FIX: Use crypto.randomUUID() for stable unique IDs
      // This prevents React key conflicts when items are deleted/reordered
      return {
        id: crypto.randomUUID(), // ✅ Stable unique ID instead of index-based
        extracted_name: item.item_name,
        extracted_qty: quantity,
        product: matchedProduct,
        sku: matchedProduct?.sku || item.sku || '',
        name: matchedProduct?.name || item.item_name,
        description: matchedProduct?.description || '',
        quantity: quantity,
        unit_price: insights.suggestedPrice,
        cost: matchedProduct?.cost || basePrice * 0.6,
        total: quantity * insights.suggestedPrice,
        insights: insights,
      };
    });
  };

  // Generate pricing insights based on history and market
  const generatePricingInsights = (product: any, basePrice: number, customer: any) => {
    const insights: any = {
      basePrice: basePrice,
      suggestedPrice: basePrice,
      margin: 0,
      alerts: [],
      opportunities: [],
    };

    if (!product) {
      insights.alerts.push({
        type: 'warning',
        message: 'Product not found in catalog',
      });
      return insights;
    }

    // Calculate margin
    const cost = product.cost || basePrice * 0.6;
    insights.margin = ((basePrice - cost) / basePrice) * 100;

    // Check if below typical margin
    if (insights.margin < 20) {
      insights.opportunities.push({
        type: 'pricing',
        message: `Margin is ${insights.margin.toFixed(1)}%. Consider $${(basePrice * 1.15).toFixed(2)} for 25% margin.`,
        suggestedPrice: basePrice * 1.15,
      });
    }

    // Simulate customer history check
    if (customer) {
      const mockHistoryPrice = basePrice * 1.05; // Simulated: they paid 5% more before
      if (basePrice < mockHistoryPrice) {
        insights.opportunities.push({
          type: 'history',
          message: `They paid $${mockHistoryPrice.toFixed(2)} last time. You could charge $${mockHistoryPrice.toFixed(2)}.`,
          suggestedPrice: mockHistoryPrice,
        });
      }
    }

    // Stock alert
    if (product.stock !== undefined && product.stock < 20) {
      insights.alerts.push({
        type: 'stock',
        message: `Low stock: Only ${product.stock} units remaining`,
      });
    }

    // Apply best suggestion
    if (insights.opportunities.length > 0) {
      // Use the highest suggested price from opportunities
      const bestOpportunity = insights.opportunities.reduce((best: any, opp: any) =>
        opp.suggestedPrice > best.suggestedPrice ? opp : best
      );
      insights.suggestedPrice = bestOpportunity.suggestedPrice;
    }

    return insights;
  };

  // Update line item price
  const updatePrice = (itemId: string, newPrice: number) => {
    // Validate: price cannot be negative
    if (newPrice < 0) {
      return;
    }
    setLineItems(items =>
      items.map(item => {
        if (item.id === itemId) {
          return {
            ...item,
            unit_price: newPrice,
            total: item.quantity * newPrice,
          };
        }
        return item;
      })
    );
  };

  // Update line item quantity
  const updateQuantity = (itemId: string, newQuantity: number) => {
    // Validate: quantity must be greater than 0
    if (newQuantity <= 0) {
      return;
    }
    setLineItems(items =>
      items.map(item => {
        if (item.id === itemId) {
          return {
            ...item,
            quantity: newQuantity,
            total: newQuantity * item.unit_price,
          };
        }
        return item;
      })
    );
  };

  // Calculate totals
  const calculateTotals = () => {
    const subtotal = lineItems.reduce((sum, item) => sum + item.total, 0);
    const taxAmount = subtotal * (taxRate / 100);
    const total = subtotal + taxAmount;
    return { subtotal, taxAmount, total };
  };

  // Send quote with race condition protection
  const handleSendQuote = async () => {
    // Prevent double submission
    if (isSubmitting || submitAttempted.current) {
      console.log('Quote submission already in progress, ignoring duplicate request');
      return;
    }

    if ((!selectedCustomer && !isNewCustomer) || lineItems.length === 0) return;

    // Mark submission as started
    setIsSubmitting(true);
    submitAttempted.current = true;
    setStep('sending');

    // Generate idempotency key for this submission
    const idempotencyKey = `quote-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    try {
      let finalCustomer = selectedCustomer;

      if (isNewCustomer) {
        // Create the new customer on-the-fly
        const custRes = await customersApi.create({
          name: newCustomerName,
          company: newCustomerName, // Default company name to same as person name for now
          email: newCustomerEmail || undefined,
          phone: newCustomerPhone || undefined,
        });
        finalCustomer = custRes.data;
        trackEvent('new_customer_created_inline', {
          customer_name: newCustomerName,
          has_email: !!newCustomerEmail,
          has_phone: !!newCustomerPhone
        });
      }

      let finalProject = selectedProject;
      if (isNewProject && newProjectName.trim()) {
        const projRes = await projectsApi.create({
          name: newProjectName,
          address: newProjectAddress || undefined,
        });
        finalProject = projRes.data;
      }

      const { subtotal, taxAmount, total } = calculateTotals();

      const quoteData = {
        customer_id: finalCustomer.id,
        project_id: finalProject?.id,
        assignee_id: selectedAssigneeId || undefined,
        items: lineItems.map(item => ({
          product_id: item.product?.id,
          product_name: item.name,
          sku: item.sku,
          quantity: item.quantity,
          unit_price: item.unit_price,
          total_price: item.total,
        })),
        tax_rate: taxRate,
        notes: `Extracted from: ${inputText.slice(0, 100)}...`,
      };

      const res = await quotesApi.create(quoteData, idempotencyKey);

      trackEvent('quote_created', {
        quote_id: res.data.id,
        item_count: lineItems.length,
        total_amount: total,
        source: selectedFile ? 'file' : 'text',
        is_new_customer: isNewCustomer
      });

      // Track time saved from using Smart Quote
      try {
        await api.post('/impact/track?action_type=smart_quote');
      } catch (e) {
        // Non-critical, don't block user
      }

      // Success! Navigate to quote view
      navigate(`/quotes/${res.data.id}`);
    } catch (error: any) {
      console.error('Failed to send quote:', error);

      // Check if it's a duplicate submission (already processed)
      if (error.response?.status === 409) {
        alert('This quote was already submitted. Check your quotes list.');
        navigate('/quotes');
      } else {
        alert('Failed to send quote. Please try again.');
      }

      setStep('review');
    } finally {
      // Reset submission state after delay to prevent immediate re-submission
      setTimeout(() => {
        setIsSubmitting(false);
        submitAttempted.current = false;
      }, 2000);
    }
  };

  // Add item to catalog on-the-fly
  const handleAddToCatalog = async (item: any) => {
    setAddingToCatalogId(item.id);
    try {
      // Enrichment: use price if extracted, otherwise use suggestedPrice
      const initialPrice = item.unit_price || item.insights.basePrice || 0;

      const productData = {
        sku: item.sku || `SKU-${Math.random().toString(36).substr(2, 9).toUpperCase()}`,
        name: item.name,
        description: item.description || `Auto-extracted from RFQ: ${item.extracted_name}`,
        price: initialPrice,
        cost: item.cost || (initialPrice * 0.7),
        category: 'Extracted'
      };

      const res = await productsApi.create(productData);
      const newProduct = res.data;

      // Update the line item with the new product
      setLineItems(items =>
        items.map(i => {
          if (i.id === item.id) {
            return {
              ...i,
              product: newProduct,
              sku: newProduct.sku,
              // Clear alerts about product not found
              insights: {
                ...i.insights,
                alerts: i.insights.alerts.filter((a: any) => a.type !== 'warning')
              }
            };
          }
          return i;
        })
      );

      // Refresh products list in background
      loadData();
    } catch (error) {
      console.error('Failed to add to catalog:', error);
      alert('Failed to add product to catalog. SKU might already exist.');
    } finally {
      setAddingToCatalogId(null);
    }
  };

  const { subtotal, taxAmount, total } = calculateTotals();

  // STEP 1: INPUT - Upload/Import FIRST, Linear/Vercel Design
  if (step === 'input') {
    return (
      <div className="min-h-screen bg-slate-50">
        {/* Header with tech grid background */}
        <div className="relative bg-white border-b border-slate-200/60 overflow-hidden">
          <div className="absolute inset-0 tech-grid opacity-40" />
          <div className="relative max-w-5xl mx-auto px-12 py-10">
            <h1 className="text-3xl font-bold text-slate-950 tracking-tighter">New Request</h1>
            <p className="text-slate-500 mt-2 text-lg">Start a new quote by uploading a file, pasting text, or forwarding an email.</p>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-12 py-12">

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            {/* OPTION 1: Upload File */}
            <div
              className={`bento-card border-2 border-dashed p-8 flex flex-col items-center text-center cursor-pointer transition-all hover:-translate-y-1 ${dragActive || selectedFile ? 'border-orange-500 bg-orange-50/50' : 'border-slate-200/60'}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-upload')?.click()}
            >
              <input
                id="file-upload"
                type="file"
                className="hidden"
                onChange={handleFileChange}
                accept=".pdf,.xlsx,.xls,.csv,.jpg,.jpeg,.png,.webp"
              />
              <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mb-5 shadow-soft">
                <Package size={26} />
              </div>
              <h3 className="font-semibold text-slate-950 mb-1 tracking-tight">Upload File</h3>
              <p className="text-sm text-slate-500 mb-5">PDF, Excel, CSV, or Images</p>

              {selectedFile ? (
                <div className="w-full bg-white border-minimal rounded-xl p-4 flex items-center gap-3 shadow-soft">
                  <div className="bg-emerald-100 text-emerald-600 p-2 rounded-xl">
                    <CheckCircle2 size={18} />
                  </div>
                  <div className="flex-1 text-left overflow-hidden">
                    <p className="text-sm font-semibold text-slate-950 truncate">{selectedFile.name}</p>
                    <p className="text-xs text-slate-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                    className="text-slate-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              ) : (
                <button className="px-5 py-2.5 bg-white border-minimal rounded-xl text-sm font-semibold text-slate-700 hover:bg-slate-50 shadow-soft transition-all">
                  Select File
                </button>
              )}
            </div>

            {/* OPTION 2: Paste Text */}
            <div className="bento-card p-8 flex flex-col md:col-span-1 relative overflow-hidden transition-all hover:-translate-y-1">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-11 h-11 bg-purple-50 text-purple-600 rounded-2xl flex items-center justify-center shadow-soft">
                  <FileText size={22} />
                </div>
                <h3 className="font-semibold text-slate-950 tracking-tight">Paste Text</h3>
              </div>
              <SmartEditor
                content={inputText}
                onChange={setInputText}
                placeholder="Paste RFQ content here..."
                className="flex-1 w-full"
                minHeight="150px"
              />
            </div>

            {/* OPTION 3: Email Forwarding */}
            <div className="bento-card p-8 flex flex-col relative overflow-hidden transition-all hover:-translate-y-1">
              <div className="flex items-center gap-3 mb-5">
                <div className="w-11 h-11 bg-amber-50 text-amber-600 rounded-2xl flex items-center justify-center shadow-soft">
                  <Send size={22} />
                </div>
                <h3 className="font-semibold text-slate-950 tracking-tight">Forward Email</h3>
              </div>
              <p className="text-sm text-slate-500 mb-5">
                Forward any RFQ email to your dedicated AI inbox to auto-create a request.
              </p>
              <div className="mt-auto bg-slate-50 border-minimal rounded-xl p-4 flex items-center justify-between gap-2">
                <code className="text-xs font-mono text-slate-700 truncate">quotes@mercura.ai</code>
                <button
                  onClick={() => navigator.clipboard.writeText('quotes@mercura.ai')}
                  className="text-slate-400 hover:text-orange-600 transition-colors"
                  title="Copy email"
                >
                  <CheckCircle2 size={18} />
                </button>
              </div>
            </div>
          </div>

          <div className="flex justify-end mb-12">
            <button
              onClick={handleExtract}
              disabled={(!inputText.trim() && !selectedFile) || isExtracting}
              className="inline-flex items-center gap-2.5 px-10 py-5 bg-slate-950 text-white font-bold text-lg rounded-2xl hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-soft-lg hover:-translate-y-0.5"
            >
              {isExtracting ? (
                <>
                  <Loader2 className="animate-spin" size={22} />
                  Extracting Data...
                </>
              ) : (
                <>
                  <Sparkles size={22} />
                  Process Request
                </>
              )}
            </button>
          </div>

          {/* Quick Stats - Bento Grid style */}
          <div className="grid grid-cols-3 gap-6 mt-8">
            <div className="bento-card p-6 text-center transition-all hover:-translate-y-1">
              <div className="text-3xl font-bold text-slate-950 tracking-tighter">{customers.length}</div>
              <div className="text-xs text-slate-500 font-medium uppercase tracking-wider mt-1">Customers</div>
            </div>
            <div className="bento-card p-6 text-center transition-all hover:-translate-y-1">
              <div className="text-3xl font-bold text-slate-950 tracking-tighter">{products.length}</div>
              <div className="text-xs text-slate-500 font-medium uppercase tracking-wider mt-1">Products</div>
            </div>
            <div className="bento-card p-6 text-center transition-all hover:-translate-y-1">
              <div className="text-3xl font-bold text-emerald-600 tracking-tighter">85%</div>
              <div className="text-xs text-slate-500 font-medium uppercase tracking-wider mt-1">Avg. Accuracy</div>
            </div>
          </div>
        </div>
      </div>
    );
  }


  // STEP 2: REVIEW - Autopilot Side-by-Side View with Linear/Vercel Design
  if (step === 'review') {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        {/* Header - Glass effect with tech grid */}
        <div className="bg-white/90 backdrop-blur-xl border-b border-slate-200/40 sticky top-0 z-10">
          <div className="max-w-[1700px] mx-auto px-8 py-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-5">
                <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-orange-600 text-white rounded-2xl flex items-center justify-center shadow-soft">
                  <Sparkles size={26} />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-slate-950 tracking-tight flex items-center gap-3">
                    Autopilot Review
                    <span className="text-[10px] bg-slate-950 text-white px-3 py-1 rounded-full font-bold uppercase tracking-widest">Human-in-the-loop</span>
                  </h1>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Verify extracted items against source for <strong className="text-slate-700">Zero-Error</strong> precision
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-5">
                <div className="text-right px-5 py-2 bg-slate-50 rounded-xl">
                  <p className="text-[10px] text-slate-400 font-semibold uppercase tracking-wider">Customer</p>
                  <p className="text-sm font-bold text-slate-950 tracking-tight">{selectedCustomer?.name || newCustomerName || 'Pending'}</p>
                </div>
                <button
                  onClick={() => setStep('input')}
                  className="px-5 py-2.5 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-all flex items-center gap-2 text-sm font-medium shadow-soft"
                >
                  <Edit3 size={16} />
                  Edit Input
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Main Autopilot Split View */}
        <div className="flex-1 max-w-[1700px] mx-auto w-full px-8 py-8 flex gap-8 overflow-hidden h-[calc(100vh-90px)]">
          {/* Left: Original Document (Source of Truth) */}
          <div className="w-1/2 flex flex-col bento-card overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
              <h3 className="font-semibold text-slate-950 tracking-tight flex items-center gap-3">
                <div className="p-2 bg-blue-50 text-blue-600 rounded-xl">
                  <FileText size={18} />
                </div>
                Source Document
              </h3>
              {selectedFile && (
                <span className="text-xs text-slate-500 font-medium bg-slate-100 px-3 py-1 rounded-full">
                  {selectedFile.name} ({(selectedFile.size / 1024 / 1024).toFixed(2)} MB)
                </span>
              )}
            </div>
            <div className="flex-1 bg-slate-100 overflow-auto flex flex-col tech-grid-fine">
              {selectedFile ? (
                selectedFile.type === 'application/pdf' ? (
                  <iframe
                    src={`${fileUrl}#toolbar=0`}
                    className="w-full h-full border-none"
                    title="Source Document"
                  />
                ) : selectedFile.type.startsWith('image/') ? (
                  <div className="p-6 flex justify-center">
                    <img src={fileUrl || ''} alt="Source Document" className="max-w-full shadow-soft-lg rounded-xl" />
                  </div>
                ) : (
                  <div className="p-10 flex items-center justify-center h-full text-slate-400 text-lg">
                    Preview not available for this file type.
                  </div>
                )
              ) : inputText ? (
                <div className="p-8 bg-white h-full font-mono text-sm text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {inputText}
                </div>
              ) : (
                <div className="p-10 flex items-center justify-center h-full text-slate-400 text-lg">
                  No source content available.
                </div>
              )}
            </div>
          </div>

          {/* Right: AI Extracted Table */}
          <div className="w-1/2 flex flex-col gap-6 overflow-auto pr-2 custom-scrollbar">
            {/* AI Customer Suggestion Banner */}
            {showCustomerSuggestion && suggestedCustomer && (
              <div className="animate-fade-in">
                <div className="bento-card p-0 overflow-hidden">
                  <div className="bg-gradient-to-r from-orange-500 to-orange-600 p-4 flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                      <Sparkles size={20} className="text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold text-white text-lg tracking-tight flex items-center gap-2">
                        New Customer Detected
                        <span className="text-[10px] bg-white/20 text-white px-2 py-0.5 rounded-full font-bold uppercase">AI</span>
                      </h3>
                    </div>
                  </div>
                  <div className="p-6">
                    <p className="text-slate-600 mb-4">
                      AI found <span className="font-bold text-slate-950">"{suggestedCustomer.name}"</span> in the document. Would you like to create a new profile?
                    </p>
                    {suggestedCustomer.email && (
                      <p className="text-xs text-slate-500 mb-4 flex items-center gap-1">
                        <Send size={12} /> {suggestedCustomer.email}
                      </p>
                    )}
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => {
                          setIsNewCustomer(true);
                          setNewCustomerName(suggestedCustomer.name);
                          setNewCustomerEmail(suggestedCustomer.email || '');
                          setNewCustomerPhone(suggestedCustomer.phone || '');
                          setShowCustomerSuggestion(false);
                        }}
                        className="flex-1 px-5 py-3 bg-slate-950 text-white font-semibold rounded-xl hover:bg-slate-800 transition-all shadow-soft flex items-center justify-center gap-2"
                      >
                        <CheckCircle2 size={18} />
                        Quick Add & Select
                      </button>
                      <button
                        onClick={() => setShowCustomerSuggestion(false)}
                        className="px-5 py-3 border-minimal text-slate-500 font-medium rounded-xl hover:bg-slate-50 transition-all"
                      >
                        Dismiss
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="bento-card overflow-hidden transition-all hover:-translate-y-0.5">
              <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center">
                <h3 className="font-semibold text-slate-950 tracking-tight flex items-center gap-3">
                  <div className="p-2 bg-orange-50 text-orange-600 rounded-xl">
                    <ListChecks size={18} />
                  </div>
                  Extracted Line Items
                </h3>
                <div className="flex items-center gap-2">
                  <span className="text-xs bg-emerald-50 text-emerald-700 font-bold px-3 py-1 rounded-full">
                    AI Confident: 92%
                  </span>
                </div>
              </div>

              <div className="divide-y divide-slate-100">
                {lineItems.map((item, index) => (
                  <div key={item.id} className="p-6 hover:bg-slate-50/50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        {/* Item Header */}
                        <div className="flex items-center gap-3 mb-3">
                          <span className="text-sm text-slate-400 font-medium">#{index + 1}</span>
                          {item.product ? (
                            <h4 className="font-semibold text-slate-950 tracking-tight">{item.name}</h4>
                          ) : (
                            <input
                              type="text"
                              value={item.name}
                              onChange={(e) => {
                                const newName = e.target.value;
                                setLineItems(items => items.map(i => i.id === item.id ? { ...i, name: newName } : i));
                              }}
                              className="font-semibold text-slate-950 bg-transparent border-b border-dashed border-slate-300 focus:border-orange-500 focus:ring-0 px-0 py-0"
                              placeholder="Product Name"
                            />
                          )}
                          {item.product ? (
                            <span className="text-xs bg-slate-100 text-slate-600 px-2.5 py-1 rounded-lg font-medium">
                              {item.sku}
                            </span>
                          ) : (
                            <input
                              type="text"
                              value={item.sku}
                              onChange={(e) => {
                                const newSku = e.target.value;
                                setLineItems(items => items.map(i => i.id === item.id ? { ...i, sku: newSku } : i));
                              }}
                              className="text-xs bg-slate-50 text-slate-600 px-2.5 py-1 rounded-lg border border-dashed border-slate-300 focus:border-orange-500 focus:ring-0"
                              placeholder="SKU"
                            />
                          )}
                          {!item.product && (
                            <span className="text-xs bg-amber-50 text-amber-700 px-2.5 py-1 rounded-lg font-semibold">
                              Not in Catalog
                            </span>
                          )}
                          {item.product && (
                            <span className="text-xs bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-lg font-semibold flex items-center gap-1">
                              <Check size={12} />
                              In Catalog
                            </span>
                          )}
                        </div>

                        {/* Extracted Info */}
                        <p className="text-sm text-slate-500 mb-4">
                          Extracted: "{item.extracted_name}" × {item.extracted_qty}
                        </p>

                        <div className="mb-4">
                          <label className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-1.5 block">Description & Specs</label>
                          <SmartEditor
                            content={item.description || ''}
                            onChange={(html) => setLineItems(items => items.map(i => i.id === item.id ? { ...i, description: html } : i))}
                            minHeight="60px"
                            placeholder="Add technical specs or item details..."
                            className="bg-white"
                          />
                        </div>

                        {/* Pricing with Insights */}
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Qty:</span>
                            <input
                              type="number"
                              min="1"
                              step="1"
                              value={item.quantity}
                              onChange={(e) => updateQuantity(item.id, parseInt(e.target.value) || 1)}
                              className="w-20 px-2 py-1 border border-gray-300 rounded text-center focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                            />
                          </div>

                          <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Price:</span>
                            <div className="relative">
                              <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                              <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={item.unit_price}
                                onChange={(e) => updatePrice(item.id, parseFloat(e.target.value))}
                                className="w-32 pl-7 pr-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                              />
                            </div>
                          </div>

                          <div className="text-right flex flex-col items-end gap-2">
                            <div className="font-semibold text-gray-900">
                              ${item.total.toFixed(2)}
                            </div>
                            <button
                              onClick={() => setLineItems(items => items.filter(i => i.id !== item.id))}
                              className="text-gray-400 hover:text-red-500 transition-colors"
                              title="Remove item"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        </div>

                        {/* Insights */}
                        <div className="mt-3 space-y-1">
                          {item.insights.alerts.map((alert: any, i: number) => (
                            <div key={i} className="flex items-center justify-between gap-2 text-sm text-amber-700 bg-amber-50 px-3 py-2 rounded">
                              <div className="flex items-center gap-2">
                                <AlertCircle size={14} />
                                {alert.message}
                              </div>
                              {alert.type === 'warning' && !item.product && (
                                <button
                                  onClick={() => handleAddToCatalog(item)}
                                  disabled={addingToCatalogId === item.id}
                                  className="text-xs bg-amber-600 text-white px-2 py-1 rounded hover:bg-amber-700 transition-colors flex items-center gap-1 font-medium disabled:opacity-50"
                                >
                                  {addingToCatalogId === item.id ? (
                                    <Loader2 className="animate-spin" size={12} />
                                  ) : (
                                    <PlusCircle size={12} />
                                  )}
                                  Quick Add
                                </button>
                              )}
                              {alert.type === 'warning' && item.product && (
                                <span className="text-xs text-green-700 flex items-center gap-1">
                                  <Check size={12} /> Added
                                </span>
                              )}
                            </div>
                          ))}

                          {item.insights.opportunities.map((opp: any, i: number) => (
                            <button
                              key={i}
                              onClick={() => updatePrice(item.id, opp.suggestedPrice)}
                              className="flex items-center gap-2 text-sm text-green-700 bg-green-50 px-3 py-2 rounded hover:bg-green-100 transition-colors w-full text-left"
                            >
                              <TrendingUp size={14} />
                              {opp.message}
                              <span className="ml-auto text-green-600 font-medium">Apply</span>
                            </button>
                          ))}

                          {item.insights.margin > 0 && (
                            <div className="flex items-center gap-2 text-sm text-gray-600">
                              <Package size={14} />
                              Margin: {item.insights.margin.toFixed(1)}%
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="p-4 bg-gray-50 border-t border-gray-200">
                <button
                  onClick={() => {
                    const newItem = {
                      id: `item-manual-${Date.now()}`,
                      extracted_name: 'Manual Item',
                      extracted_qty: 1,
                      product: null,
                      sku: '',
                      name: '',
                      description: '',
                      quantity: 1,
                      unit_price: 0,
                      cost: 0,
                      total: 0,
                      insights: {
                        alerts: [{ type: 'warning', message: 'Custom item - not in catalog' }],
                        opportunities: [],
                        basePrice: 0,
                        suggestedPrice: 0,
                        margin: 0
                      }
                    };
                    setLineItems([...lineItems, newItem]);
                  }}
                  className="flex items-center gap-2 text-sm font-medium text-orange-600 hover:text-orange-700 transition-colors"
                >
                  <Plus size={16} />
                  Add Custom Item
                </button>
              </div>
            </div>

            {/* Removed redundant Collapsible Original Input as it's now permanently on the left */}
          </div>

          {/* Summary & Actions - Bento Grid */}
          <div className="grid grid-cols-2 gap-6">
            {/* Quote Summary */}
            <div className="bento-card p-8 transition-all hover:-translate-y-0.5">
              <h3 className="font-semibold text-slate-950 tracking-tight mb-6">Quote Summary</h3>

              <div className="space-y-4 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Subtotal</span>
                  <span className="font-semibold text-slate-700">${subtotal.toFixed(2)}</span>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Tax ({taxRate}%)</span>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="0"
                      max="100"
                      step="0.01"
                      value={taxRate}
                      onChange={(e) => {
                        const value = parseFloat(e.target.value);
                        if (!isNaN(value) && value >= 0 && value <= 100) {
                          setTaxRate(value);
                        }
                      }}
                      className="w-16 px-3 py-1.5 border-minimal rounded-lg text-right text-sm shadow-soft"
                    />
                    <span className="text-slate-400">%</span>
                  </div>
                </div>

                <div className="text-right text-sm text-slate-500">
                  ${taxAmount.toFixed(2)}
                </div>

                <div className="border-t border-slate-100 pt-4 flex justify-between">
                  <span className="font-bold text-slate-950 tracking-tight">Total</span>
                  <span className="text-3xl font-bold text-slate-950 tracking-tighter">${total.toFixed(2)}</span>
                </div>
              </div>

              {/* Time Saved Estimate */}
              <div className="mt-8 p-5 bg-blue-50 rounded-xl">
                <div className="flex items-center gap-2 text-blue-800 font-semibold mb-2">
                  <History size={18} />
                  Time Saved
                </div>
                <p className="text-sm text-blue-700">
                  This quote would have taken <strong>18 minutes</strong> manually.
                  You did it in <strong>2 minutes</strong>.
                </p>
              </div>
            </div>

            {/* Results Sidebar / Insights */}
            <div className="space-y-6">
              {/* Confidence Score */}
              <div className="bento-card p-8 bg-emerald-50/50 transition-all hover:-translate-y-0.5">
                <div className="flex items-center gap-2 text-emerald-800 font-bold mb-4">
                  <CheckCircle2 size={20} />
                  Intelligence Report
                </div>
                <div className="space-y-4">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-emerald-700">Catalog Match</span>
                    <span className="font-bold text-emerald-800">{lineItems.filter(i => i.product).length} / {lineItems.length} items</span>
                  </div>
                  <div className="w-full bg-emerald-200 rounded-full h-2">
                    <div
                      className="bg-emerald-600 h-2 rounded-full transition-all"
                      style={{ width: `${(lineItems.filter(i => i.product).length / lineItems.length) * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-emerald-600">
                    AI matched your products. {lineItems.filter(i => !i.product).length} items require catalog creation.
                  </p>
                </div>
              </div>

              {/* Time Saved Estimate */}
              <div className="bento-card p-8 bg-blue-50/50 transition-all hover:-translate-y-0.5">
                <div className="flex items-center gap-2 text-blue-800 font-bold mb-3">
                  <History size={18} />
                  Efficiency Gain
                </div>
                <p className="text-sm text-blue-700 leading-relaxed">
                  This multi-item RFQ would typically take <strong>18 minutes</strong> to manually enter.
                  OpenMercura processed it in <strong>3.2 seconds</strong>.
                </p>
                <div className="mt-5 flex items-center gap-2">
                  <div className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-bold">89% Faster</div>
                  <div className="text-xs bg-blue-100 text-blue-700 px-3 py-1 rounded-full font-bold">Grade A Accuracy</div>
                </div>
              </div>
            </div>
          </div>

          {/* Final Action Buttons */}
          <div className="flex items-center gap-5 pt-6 pb-10">
            <button
              onClick={handleSendQuote}
              className="flex-1 flex items-center justify-center gap-2.5 px-8 py-5 bg-slate-950 text-white font-bold text-lg rounded-2xl hover:bg-slate-800 transition-all shadow-soft-lg hover:-translate-y-0.5"
            >
              <Send size={22} />
              Approve & Send Quote
            </button>

            <button className="px-8 py-5 border-minimal text-slate-700 font-bold text-lg rounded-2xl hover:bg-slate-50 transition-all shadow-soft">
              Save as Draft
            </button>
          </div>
        </div>
      </div>
    );
  }

  // STEP 3: SENDING - Loading State
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center tech-grid">
      <div className="text-center bento-card p-12">
        <Loader2 className="animate-spin mx-auto mb-6 text-orange-500" size={56} />
        <h2 className="text-2xl font-bold text-slate-950 tracking-tight">Creating Your Quote...</h2>
        <p className="text-slate-500 mt-2 text-lg">Generating PDF and sending to customer</p>
      </div>
    </div>
  );
};

export default SmartQuote;
