import type { components } from './generated'

export type Vehicle = components['schemas']['Vehicle']
export type VehicleList = components['schemas']['VehicleList']
export type Trip = components['schemas']['Trip']
export type TripList = components['schemas']['TripList']
export type Summary = components['schemas']['Summary']
export type Alert = components['schemas']['Alert']
export type AlertList = components['schemas']['AlertList']
export type DataSource = VehicleList['source']
export type TripUpdate = components['schemas']['TripUpdate']
