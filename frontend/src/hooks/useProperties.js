import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchProperties } from "../services/api.js";

export const DEFAULT_FILTERS = {
  minPrice: null,
  maxPrice: null,
  minSurface: null,
  maxSurface: null,
  minExterior: null,
  maxExterior: null,
  maxTrainWalk: null,
  maxBusWalk: null,
  maxTramWalk: null,
  department: "all",
  propertyType: null,
  source: null,
};

export function useProperties() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [selectedId, setSelectedId] = useState(null);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["properties", filters],
    queryFn: () => fetchProperties(filters),
    keepPreviousData: true,
  });

  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  return {
    properties: data?.results ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    error,
    filters,
    updateFilter,
    resetFilters,
    refetch,
    selectedId,
    setSelectedId,
  };
}
