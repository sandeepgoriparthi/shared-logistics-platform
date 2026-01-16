"use client"

import { useState } from "react"
import { useForm, FormProvider } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { OriginStep } from "./steps/origin-step"
import { DestinationStep } from "./steps/destination-step"
import { FreightStep } from "./steps/freight-step"
import { ReviewStep } from "./steps/review-step"
import { StepIndicator } from "./step-indicator"

const shipmentSchema = z.object({
  // Origin
  originAddress: z.string().min(1, "Address is required"),
  originCity: z.string().min(1, "City is required"),
  originState: z.string().min(1, "State is required"),
  originZip: z.string().min(5, "ZIP code is required"),
  pickupDate: z.date({ required_error: "Pickup date is required" }),
  pickupTimeFrom: z.string().min(1, "Pickup time is required"),
  pickupTimeTo: z.string().min(1, "Pickup time is required"),
  originContact: z.string().min(1, "Contact name is required"),
  originPhone: z.string().min(10, "Phone number is required"),
  originInstructions: z.string().optional(),

  // Destination
  destAddress: z.string().min(1, "Address is required"),
  destCity: z.string().min(1, "City is required"),
  destState: z.string().min(1, "State is required"),
  destZip: z.string().min(5, "ZIP code is required"),
  deliveryDate: z.date({ required_error: "Delivery date is required" }),
  deliveryTimeFrom: z.string().min(1, "Delivery time is required"),
  deliveryTimeTo: z.string().min(1, "Delivery time is required"),
  destContact: z.string().min(1, "Contact name is required"),
  destPhone: z.string().min(10, "Phone number is required"),
  appointmentRequired: z.boolean().default(false),
  liftgateRequired: z.boolean().default(false),
  destInstructions: z.string().optional(),

  // Freight
  weight: z.number().min(1, "Weight is required"),
  length: z.number().min(1, "Length is required"),
  width: z.number().min(1, "Width is required"),
  height: z.number().min(1, "Height is required"),
  linearFeet: z.number().min(1).max(53),
  palletCount: z.number().min(1, "Pallet count is required"),
  equipmentType: z.string().min(1, "Equipment type is required"),
  commodityType: z.string().min(1, "Commodity type is required"),
  stackable: z.boolean().default(false),
  hazmat: z.boolean().default(false),
})

export type ShipmentFormData = z.infer<typeof shipmentSchema>

const steps = [
  { id: 1, title: "Origin", description: "Pickup location" },
  { id: 2, title: "Destination", description: "Delivery location" },
  { id: 3, title: "Freight", description: "Cargo details" },
  { id: 4, title: "Review", description: "Confirm & book" },
]

export function ShipmentForm() {
  const [currentStep, setCurrentStep] = useState(1)

  const form = useForm<ShipmentFormData>({
    resolver: zodResolver(shipmentSchema),
    defaultValues: {
      originAddress: "",
      originCity: "",
      originState: "",
      originZip: "",
      pickupTimeFrom: "08:00",
      pickupTimeTo: "17:00",
      originContact: "",
      originPhone: "",
      originInstructions: "",
      destAddress: "",
      destCity: "",
      destState: "",
      destZip: "",
      deliveryTimeFrom: "08:00",
      deliveryTimeTo: "17:00",
      destContact: "",
      destPhone: "",
      appointmentRequired: false,
      liftgateRequired: false,
      destInstructions: "",
      weight: 0,
      length: 48,
      width: 40,
      height: 48,
      linearFeet: 6,
      palletCount: 1,
      equipmentType: "",
      commodityType: "",
      stackable: false,
      hazmat: false,
    },
  })

  const nextStep = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const onSubmit = (data: ShipmentFormData) => {
    console.log("Shipment booked:", data)
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-foreground mb-2">Create New Shipment</h1>
        <p className="text-muted-foreground">Fill out the details below to book your freight shipment</p>
      </div>

      <StepIndicator steps={steps} currentStep={currentStep} />

      <FormProvider {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          {currentStep === 1 && <OriginStep onNext={nextStep} />}
          {currentStep === 2 && <DestinationStep onNext={nextStep} onBack={prevStep} />}
          {currentStep === 3 && <FreightStep onNext={nextStep} onBack={prevStep} />}
          {currentStep === 4 && <ReviewStep onBack={prevStep} />}
        </form>
      </FormProvider>
    </div>
  )
}
